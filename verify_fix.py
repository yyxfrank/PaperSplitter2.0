"""验证修复结果"""
import sqlite3
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "webapp"))
from database.database import DB_PATH

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

print("=" * 70)
print("  Verify image_path fix")
print("=" * 70)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print()
print("After fix:")
rows = conn.execute("SELECT * FROM questions").fetchall()
for r in rows:
    full = os.path.join(PROJECT_ROOT, r['image_path'])
    exists = os.path.exists(full)
    status = "OK" if exists else "MISSING"
    print(f"  [{status}] {r['topic_id']} Q{r['question_number']}: {r['image_path']}")

conn.close()
print()
print("=" * 70)
