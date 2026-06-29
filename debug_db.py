"""Diagnostic: check current database state"""
import sqlite3
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "webapp"))
from database.database import DB_PATH

print("=" * 70)
print("  Database Diagnostic")
print("=" * 70)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# 1. Show all distinct paper_names
print("\n[1] All paper_names in questions table:")
papers = conn.execute("SELECT DISTINCT paper_name FROM questions ORDER BY paper_name").fetchall()
print(f"    Found {len(papers)} unique paper names:")
for p in papers:
    count = conn.execute("SELECT COUNT(*) FROM questions WHERE paper_name = ?", (p['paper_name'],)).fetchone()[0]
    print(f"    - {p['paper_name']} ({count} questions)")

# 2. Check if there's an ENGAA_2018 pattern
print("\n[2] Search for any 2018-related paper name:")
rows = conn.execute("SELECT * FROM questions WHERE paper_name LIKE '%2018%'").fetchall()
print(f"    Found {len(rows)} rows with paper_name LIKE '%2018%'")
if rows:
    for r in rows:
        print(f"      - {r['paper_name']} Q{r['question_number']} ({r['topic_id']})")

# 3. Show table schema
print("\n[3] Table schema for questions:")
schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='questions'").fetchone()
print(f"    {schema[0]}")

# 4. Check unique index/constraint
print("\n[4] Check uniqueness constraints (paper_name + question_number):")
duplicates = conn.execute("""
    SELECT paper_name, question_number, COUNT(*) as cnt
    FROM questions
    GROUP BY paper_name, question_number
    HAVING cnt > 1
""").fetchall()
if duplicates:
    print("    Found duplicates:")
    for d in duplicates:
        print(f"    - {d['paper_name']} Q{d['question_number']} appears {d['cnt']} times")
else:
    print("    No duplicate entries found (good).")

# 5. Check all question numbers per paper
print("\n[5] Per-paper question number ranges:")
for p in papers:
    pn = p['paper_name']
    min_q = conn.execute("SELECT MIN(question_number) FROM questions WHERE paper_name = ?", (pn,)).fetchone()[0]
    max_q = conn.execute("SELECT MAX(question_number) FROM questions WHERE paper_name = ?", (pn,)).fetchone()[0]
    count = conn.execute("SELECT COUNT(*) FROM questions WHERE paper_name = ?", (pn,)).fetchone()[0]
    print(f"    {pn}: Q{min_q} to Q{max_q} ({count} questions)")

# 6. output_questions directory
print("\n[6] output_questions directory:")
output_dir = os.path.join(os.path.dirname(DB_PATH), "output_questions")
if os.path.exists(output_dir):
    for d in sorted(os.listdir(output_dir)):
        full = os.path.join(output_dir, d)
        if os.path.isdir(full):
            files = os.listdir(full)
            print(f"    {d}/  ({len(files)} files)")
else:
    print("    Directory not found.")

# 7. Check if ENGAA_2018_S1 files exist
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
