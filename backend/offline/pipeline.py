"""
Pipeline: 一键处理整套试卷
===================================
把 4 个步骤串联为一次运行：
  1. AI_question_translator  →  AI 分类题目
  2. Question_extractor      →  裁剪 PDF → PNG
  3. Blank_remover           →  修剪图片空白
  4. build_database          →  写入 SQLite

用法：
    python backend/offline/pipeline.py <PDF路径>

示例：
    python backend/offline\pipeline.py ExperiData\ENGAA_2018_S1_QuestionPaper.pdf

可选参数：
    --syllabus  大纲 JSON 路径（默认 structured_syllabus_physics.json）
    --classified  分类结果 JSON 路径（默认 classified_questions_physics.json）
    --db         数据库路径（默认 master_exam_data.db）
"""

import os
import sys
import json
import argparse

# ── 确保能从子目录 import 函数 ──
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_EXTRACTORS_DIR = os.path.join(_THIS_DIR, "extractors")
_LOADERS_DIR = os.path.join(_THIS_DIR, "loaders")
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))

for _p in [_EXTRACTORS_DIR, _LOADERS_DIR, _PROJECT_ROOT]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# 切换到项目根目录，使所有相对路径（output_questions/ 等）生效
os.chdir(_PROJECT_ROOT)


def step_header(step_num, total, title):
    """打印一个醒目的步骤标题"""
    print()
    print("=" * 65)
    print(f"  步骤 {step_num}/{total}：{title}")
    print("=" * 65)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="一键处理整套试卷：AI 分类 → 裁剪 PNG → 修剪空白 → 写入数据库"
    )
    parser.add_argument(
        "pdf_path",
        help="试卷 PDF 路径（相对或绝对路径均可）",
    )
    parser.add_argument(
        "--syllabus",
        default="structured_syllabus_physics.json",
        help="大纲 JSON 文件（默认 structured_syllabus_physics.json）",
    )
    parser.add_argument(
        "--classified",
        default="classified_questions_physics.json",
        help="AI 分类结果 JSON 输出文件（默认 classified_questions_physics.json）",
    )
    parser.add_argument(
        "--db",
        default="master_exam_data.db",
        help="SQLite 数据库路径（默认 master_exam_data.db）",
    )
    args = parser.parse_args()

    # 统一成绝对路径，避免后续 CD 变化导致路径失效
    pdf_path = os.path.abspath(args.pdf_path)
    if not os.path.exists(pdf_path):
        print(f"❌ 找不到 PDF 文件：{pdf_path}")
        sys.exit(1)

    syllabus_path = os.path.abspath(args.syllabus) if not os.path.isabs(args.syllabus) else args.syllabus
    classified_path = os.path.abspath(args.classified) if not os.path.isabs(args.classified) else args.classified
    db_path = os.path.abspath(args.db) if not os.path.isabs(args.db) else args.db

    print(f"📂 项目根目录：{_PROJECT_ROOT}")
    print(f"📄 试卷：{pdf_path}")
    print(f"📋 大纲：{syllabus_path}")
    print(f"📦 数据库：{db_path}")

    total_steps = 4

    # ────────────────────────────────────────────────────────────
    # STEP 1: AI_question_translator — AI 分类题目
    # ────────────────────────────────────────────────────────────
    step_header(1, total_steps, "AI 分类题目")
    from AI_question_translator import process_and_classify_exam

    # 注意：AI_question_translator 里会弹 input() 让输入 API Key
    json_data = process_and_classify_exam(pdf_path, syllabus_path)

    with open(classified_path, "w", encoding="utf-8") as f:
        f.write(json_data)

    # 解析并打印统计信息
    classified_data = json.loads(json_data)
    print(f"\n✅ AI 分类完成！共 {len(classified_data)} 道题")
    print(f"📁 分类结果已保存到：{classified_path}")

    # ────────────────────────────────────────────────────────────
    # STEP 2: Question_extractor — 裁剪 PDF 为 PNG
    # ────────────────────────────────────────────────────────────
    step_header(2, total_steps, "裁剪 PDF → PNG")
    from Question_extractor import extract_paper_name_from_filename, auto_slice_entire_exam

    paper_name = extract_paper_name_from_filename(pdf_path)
    print(f"📛 试卷名称：{paper_name}")

    total_questions = auto_slice_entire_exam(pdf_path, paper_name)
    print(f"\n✅ 裁剪完成！共 {total_questions} 张 PNG")

    # ────────────────────────────────────────────────────────────
    # STEP 3: Blank_remover — 修剪图片底部空白
    # ────────────────────────────────────────────────────────────
    step_header(3, total_steps, "修剪 PNG 底部空白")
    from Blank_remover import batch_trim_folder

    output_folder = os.path.join(_PROJECT_ROOT, "output_questions")
    print(f"🗂️  修剪目录：{output_folder}")
    batch_trim_folder(output_folder)
    print(f"✅ 修剪完成！")

    # ────────────────────────────────────────────────────────────
    # STEP 4: build_database — 写入 SQLite
    # ────────────────────────────────────────────────────────────
    step_header(4, total_steps, "写入 SQLite 数据库")
    from build_database import append_to_database

    image_folder = "output_questions"
    append_to_database(
        paper_name=paper_name,
        syllabus_json=syllabus_path,
        classified_json=classified_path,
        image_folder=image_folder,
        db_name=db_path,
    )

    # ────────────────────────────────────────────────────────────
    # 完成
    # ────────────────────────────────────────────────────────────
    print()
    print("=" * 65)
    print("  🎉 全部完成！4 个步骤均执行成功！")
    print("=" * 65)
    print(f"\n📊 试卷：{paper_name}")
    print(f"📝 题目数：{total_questions}")
    print(f"🗄️  数据库：{db_path}")
    print(f"\n💡 现在可以重启 Flask 服务器查看最新数据了：")


if __name__ == "__main__":
    main()
