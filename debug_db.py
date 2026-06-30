"""
诊断脚本：检查 MySQL 数据库当前状态（MySQL 版）
================================================
语法差异：
  - sqlite_master → INFORMATION_SCHEMA 或 SHOW CREATE TABLE
  - 其他查询语法基本不变
"""
import mysql.connector
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "webapp"))
from database.db_config import DB_CONFIG

print("=" * 70)
print("  Database Diagnostic (MySQL)")
print("=" * 70)

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

# 1. 显示所有不重复的 paper_name
print("\n[1] All paper_names in questions table:")
cursor.execute("SELECT DISTINCT paper_name FROM questions ORDER BY paper_name")
papers = cursor.fetchall()
print(f"    Found {len(papers)} unique paper names:")
for p in papers:
    cursor.execute("SELECT COUNT(*) as cnt FROM questions WHERE paper_name = %s", (p['paper_name'],))
    count = cursor.fetchone()['cnt']
    print(f"    - {p['paper_name']} ({count} questions)")

# 2. 查找 2018 相关数据
print("\n[2] Search for any 2018-related paper name:")
cursor.execute("SELECT * FROM questions WHERE paper_name LIKE %s", ('%2018%',))
rows = cursor.fetchall()
print(f"    Found {len(rows)} rows with paper_name LIKE '%2018%'")
for r in rows:
    print(f"      - {r['paper_name']} Q{r['question_number']} ({r['topic_id']})")

# 3. 显示表结构（MySQL 语法：SHOW CREATE TABLE）
print("\n[3] Table schema for questions:")
cursor.execute("SHOW CREATE TABLE questions")
row = cursor.fetchone()
print(f"    {row['Create Table']}")

# 4. 检查唯一约束
print("\n[4] Check uniqueness constraints (paper_name + question_number):")
cursor.execute("""
    SELECT paper_name, question_number, COUNT(*) as cnt
    FROM questions
    GROUP BY paper_name, question_number
    HAVING cnt > 1
""")
duplicates = cursor.fetchall()
if duplicates:
    print("    Found duplicates:")
    for d in duplicates:
        print(f"    - {d['paper_name']} Q{d['question_number']} appears {d['cnt']} times")
else:
    print("    No duplicate entries found (good).")

# 5. 查看各试卷题号范围
print("\n[5] Per-paper question number ranges:")
for p in papers:
    pn = p['paper_name']
    cursor.execute("SELECT MIN(question_number) as min_q FROM questions WHERE paper_name = %s", (pn,))
    min_q = cursor.fetchone()['min_q']
    cursor.execute("SELECT MAX(question_number) as max_q FROM questions WHERE paper_name = %s", (pn,))
    max_q = cursor.fetchone()['max_q']
    cursor.execute("SELECT COUNT(*) as cnt FROM questions WHERE paper_name = %s", (pn,))
    count = cursor.fetchone()['cnt']
    print(f"    {pn}: Q{min_q} to Q{max_q} ({count} questions)")

# 6. output_questions 目录检查（与数据库无关，保持原样）
print("\n[6] output_questions directory:")
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
output_dir = os.path.join(_PROJECT_ROOT, "output_questions")
if os.path.exists(output_dir):
    for d in sorted(os.listdir(output_dir)):
        full = os.path.join(output_dir, d)
        if os.path.isdir(full):
            files = os.listdir(full)
            print(f"    {d}/  ({len(files)} files)")
else:
    print("    Directory not found.")

# 7. 检查 2018 文件
print("\n[7] Check if 2018 files exist on disk:")
target = os.path.join(output_dir, "ENGAA_2018_S1")
if os.path.exists(target):
    files = os.listdir(target)
    print(f"    ENGAA_2018_S1 exists with {len(files)} files:")
    for f in sorted(files)[:5]:
        print(f"      - {f}")
    if len(files) > 5:
        print(f"      ... total {len(files)}")
else:
    print(f"    ENGAA_2018_S1 not found on disk: {target}")

conn.close()
print("\n" + "=" * 70)
