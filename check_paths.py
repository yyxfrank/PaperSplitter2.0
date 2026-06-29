"""Check current image_path state"""
import sqlite3
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "webapp"))
from database.database import DB_PATH

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("=" * 70)
print("  Current image_path check (by paper)")
print("=" * 70)

papers = conn.execute("SELECT DISTINCT paper_name FROM questions ORDER BY paper_name").fetchall()

for p in papers:
    pn = p['paper_name']
    sample = conn.execute(
        "SELECT image_path FROM questions WHERE paper_name = ? LIMIT 1",
        (pn,)
    ).fetchone()
    count = conn.execute(
        "SELECT COUNT(*) FROM questions WHERE paper_name = ?",
        (pn,)
    ).fetchone()[0]
    
    print(f"\n  [{pn}] {count} questions")
    print(f"    sample image_path = {sample['image_path']}")
    
    # Check if this path actually exists on disk
    full_path = os.path.join(PROJECT_ROOT, sample['image_path'])
    print(f"    exists on disk? {os.path.exists(full_path)}")
    
    # Check all paths for this paper
    all_exist = True
    missing = []
    for q in conn.execute(
        "SELECT * FROM questions WHERE paper_name = ?",
        (pn,)
    ).fetchall():
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
for d in sorted(os.listdir(output_dir)):
    if os.path.isdir(os.path.join(output_dir, d)):
        files = os.listdir(os.path.join(output_dir, d))
        print(f"    {d}/  ({len(files)} PNG files)")

conn.close()
print("\n" + "=" * 70)
