"""检查当前 image_path 状态（MySQL 版）"""
import mysql.connector
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "webapp"))
from database.db_config import DB_CONFIG

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

print("=" * 70)
print("  Current image_path check (by paper)")
print("=" * 70)

cursor.execute("SELECT DISTINCT paper_name FROM questions ORDER BY paper_name")
papers = cursor.fetchall()

for p in papers:
    pn = p['paper_name']
    cursor.execute(
        "SELECT image_path FROM questions WHERE paper_name = %s LIMIT 1",
        (pn,)
    )
    sample = cursor.fetchone()
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM questions WHERE paper_name = %s",
        (pn,)
    )
    count = cursor.fetchone()['cnt']

    print(f"\n  [{pn}] {count} questions")
    if sample:
        print(f"    sample image_path = {sample['image_path']}")

        # Check if this path actually exists on disk
        full_path = os.path.join(PROJECT_ROOT, sample['image_path'])
        print(f"    exists on disk? {os.path.exists(full_path)}")

        # Check all paths for this paper
        all_exist = True
        missing = []
        cursor.execute(
            "SELECT * FROM questions WHERE paper_name = %s",
            (pn,)
        )
        for q in cursor.fetchall():
            fp = os.path.join(PROJECT_ROOT, q['image_path'])
            if not os.path.exists(fp):
                all_exist = False
                missing.append(f"Q{q['question_number']} -> {q['image_path']}")

        if all_exist:
            print("    All image paths OK")
        else:
            print(f"    {len(missing)} paths MISSING!")
            for m in missing[:5]:
                print(f"      - {m}")

# Show directories on disk
print(f"\n  Directories in output_questions/:")
output_dir = os.path.join(PROJECT_ROOT, "output_questions")
if os.path.exists(output_dir):
    for d in sorted(os.listdir(output_dir)):
        full = os.path.join(output_dir, d)
        if os.path.isdir(full):
            files = os.listdir(full)
            print(f"    {d}/  ({len(files)} PNG files)")

conn.close()
print("\n" + "=" * 70)
