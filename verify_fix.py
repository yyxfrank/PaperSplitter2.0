"""验证修复结果（MySQL 版）"""
import mysql.connector
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "webapp"))
from database.db_config import DB_CONFIG

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

print("=" * 70)
print("  Verify image_path fix")
print("=" * 70)

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

print()
print("After fix:")
cursor.execute("SELECT * FROM questions")
rows = cursor.fetchall()
for r in rows:
    full = os.path.join(PROJECT_ROOT, r['image_path'])
    exists = os.path.exists(full)
    status = "OK" if exists else "MISSING"
    print(f"  [{status}] {r['topic_id']} Q{r['question_number']}: {r['image_path']}")

conn.close()
print()
print("=" * 70)
