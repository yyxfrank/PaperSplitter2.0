"""
答案录入工具
============
从 *_answer_key.pdf 中提取答案表格，写入对应学科的 questions 表。
支持一个答案文件包含多个表格（如左右双栏），也支持同一试卷
（如 ENGAA 数学物理混考）同时更新 physics 和 math 两个库。

典型用法：
    # 纯物理卷
    python load_answer_keys.py --paper "PAT_2020" --pdf "PAT_2020_answer_key.pdf"

    # 纯数学卷
    python load_answer_keys.py --paper "MAT_2020" --pdf "MAT_2020_answer_key.pdf"

    # 数理混考卷（如 ENGAA），同时写入两个学科的表
    python load_answer_keys.py --paper "ENGAA_2023_S1" --pdf "ENGAA_2023_S1_answer_key.pdf"

    # 手动指定学科（跳过自动推断）
    python load_answer_keys.py --paper "..." --pdf "....pdf" --subjects physics,math

    # 只更新数学表
    python load_answer_keys.py --paper "..." --pdf "....pdf" --subjects math

PDF 格式要求：
    每个表格第一列是题号（整数），第二列是答案（如 A/B/C/D）。
    表头行会被自动跳过。多个表格的结果会合并（后覆盖前）。

依赖：pip install pdfplumber
"""
import argparse
import os
import re
import sys

import pdfplumber

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "webapp"))
from database.db_config import DB_CONFIG
import mysql.connector
from mysql.connector import Error as MySQLError


# ── 学科/表名映射 ────────────────────────────────────────────────
_SUBJECT_TABLES = {
    "physics": "questions_physics",
    "math": "questions_math",
}

# 从 paper_name 推断学科的规则
# (pattern, matched_subjects_list)
# 返回 list 以支持数理混考卷（如 ENGAA 同时匹配 physics 和 math）
_PAPER_SUBJECT_RULES = [
    (r"(?i)engaa",               ["physics", "math"]),   # ENGAA 数理混考
    (r"(?i)pat|physics",         ["physics"]),
    (r"(?i)tmua|math",           ["math"]),
]


def guess_subjects(paper_name: str) -> list[str]:
    """根据 paper_name 猜测学科列表。

    按 _PAPER_SUBJECT_RULES 顺序匹配，返回第一个匹配规则的学科列表。
    若全部不匹配则返回空列表。

    返回示例:
      "ENGAA_2023_S1" → ["physics", "math"]   （混考）
      "PAT_2020"      → ["physics"]
      "MAT_2020"      → ["math"]
    """
    for pattern, subjects in _PAPER_SUBJECT_RULES:
        if re.search(pattern, paper_name):
            return list(subjects)
    return []


def _parse_single_table(table) -> dict[int, str]:
    """从一个 pdfplumber 表格行中提取答案映射。

    table: pdfplumber.extract_tables() 返回的单表数据（list[list[str]]）

    返回: {1: "A", 2: "C", ...}
    """
    answers: dict[int, str] = {}
    for row in table:
        if not row or len(row) < 2:
            continue

        q_str = str(row[0]).strip()
        a_str = str(row[1]).strip()

        # 跳过空行和表头行
        if not q_str or not a_str:
            continue
        # 支持 "Q1" 和 "1" 两种题号格式（2020 年后的答案表使用 Q 前缀）
        q_clean = q_str.lstrip("Qq").strip()
        if not q_clean.isdigit():
            continue

        q_num = int(q_clean)
        # 答案只取第一个字母（如 "A" 或 "A " 或 "A (1 mark)"）
        answer = a_str[0].upper()
        if answer in "ABCDEFGH":
            answers[q_num] = answer

    return answers


def extract_answers(pdf_path: str) -> dict[int, str]:
    """从答案 PDF 的**所有页的所有表格**中提取 (题号 → 答案) 映射。

    每个表格独立解析（第一列题号，第二列答案），结果合并。
    如果后续表格与前面有相同题号，后面的值覆盖前面的（后覆盖前）。
    返回: {1: "A", 2: "C", 3: "B", ...}
    空 dict 表示提取失败。
    """
    if not os.path.isfile(pdf_path):
        print(f"  ⚠ 文件不存在: {pdf_path}")
        return {}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                print(f"  ⚠ PDF 无页面: {pdf_path}")
                return {}

            answers: dict[int, str] = {}

            for page_idx, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if not tables:
                    continue

                
                for ti, table in enumerate(tables):
                    parsed = _parse_single_table(table)
                    answers.update(parsed)
                    print(f"  📄 第{page_idx + 1}页·表格{ti + 1}: {len(parsed)} 题")

            if not answers:
                print(f"  ⚠ 在所有页的表格中均未提取到有效的 (题号, 答案) 对")

            return answers

    except Exception as e:
        print(f"  ❌ PDF 解析失败: {e}")
        return {}


def update_database(paper_name: str, answers: dict[int, str],
                    subjects: list[str]):
    """将答案写入指定学科列表的 questions 表。

    参数:
      paper_name: 试卷名称
      answers:    {题号: 答案} 映射
      subjects:   学科列表，如 ["physics", "math"]

    对每个学科分别执行 UPDATE … WHERE paper_name= AND question_number=。
    幂等设计：答案已存在会被覆盖；题号不在该表中则跳过（不报错）。
    """
    # ── 过滤出已知学科 ────────────────────────────────────────
    valid = [(s, _SUBJECT_TABLES[s]) for s in subjects if s in _SUBJECT_TABLES]
    if not valid:
        print(f"  ❌ 学科列表 {subjects} 均为未知学科，可用: {list(_SUBJECT_TABLES)}")
        return

    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            charset=DB_CONFIG["charset"],
            collation=DB_CONFIG["collation"],
            use_pure=DB_CONFIG["use_pure"],
        )
    except MySQLError as e:
        print(f"  ❌ MySQL 连接失败: {e}")
        return

    cursor = conn.cursor()

    for subject, q_tbl in valid:
        updated = 0
        not_found = 0

        for q_num, answer in answers.items():
            cursor.execute(
                f"UPDATE {q_tbl} SET answer = %s "
                "WHERE paper_name = %s AND question_number = %s",
                (answer, paper_name, q_num),
            )
            if cursor.rowcount > 0:
                updated += 1
            else:
                not_found += 1

        print(f"  📋 {subject} ({q_tbl}): 更新 {updated} 题", end="")
        if not_found:
            print(f"，{not_found} 题未找到（属于另一学科或不存在）", end="")
        print()

    conn.commit()
    conn.close()


def run(paper: str, pdf_path: str, subjects: list[str] | None = None):
    """编程调用入口：从答案 PDF 提取答案并写入数据库。

    参数:
      paper:     试卷名称，如 "ENGAA_2023_S1"
      pdf_path:  答案 PDF 文件路径
      subjects:  学科列表，如 ["physics", "math"]。
                留空则从 paper 名称自动推断。
    """
    # ── 1. 推断学科列表 ──────────────────────────────────────
    if subjects:
        subjects = list(subjects)
    else:
        subjects = guess_subjects(paper) or ["physics"]

    print(f"Paper: {paper}")
    print(f"Subjects: {', '.join(subjects)}")

    # ── 2. 提取答案（所有页、所有表格） ───────────────────────
    answers = extract_answers(pdf_path)
    if not answers:
        print("⚠ 没有提取到任何答案，退出。")
        return

    print(f"\n共提取到 {len(answers)} 个答案: "
          f"Q{min(answers)}–Q{max(answers)}")

    # ── 3. 写入数据库 ─────────────────────────────────────────
    update_database(paper, answers, subjects)


def main():
    parser = argparse.ArgumentParser(
        description="从答案 PDF 导入答案到数据库（支持多表格、多学科）"
    )
    parser.add_argument("--paper", required=True, help="试卷名称，如 ENGAA_2023_S1")
    parser.add_argument("--pdf", required=True, help="答案 PDF 文件路径")
    parser.add_argument(
        "--subjects",
        help="学科列表，逗号分隔（如 'physics,math'）。"
             "留空则从 paper_name 自动推断；ENGAA 会自动推断为 physics,math",
    )
    args = parser.parse_args()

    subjects = None
    if args.subjects:
        subjects = [s.strip() for s in args.subjects.split(",") if s.strip()]

    run(paper=args.paper, pdf_path=args.pdf, subjects=subjects)


if __name__ == "__main__":
    main()
