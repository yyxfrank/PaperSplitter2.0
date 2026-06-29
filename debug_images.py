import sqlite3
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "webapp"))
from database.database import DB_PATH, IMAGE_BASE_DIR, get_all_topics

print("=" * 70)
print("  PaperSplitter 图片路径调试")
print("=" * 70)

# ── 1. 打印各种关键路径 ─────────────────────────────────────
print(f"\n[1] 关键路径信息：")
print(f"    项目根目录 (IMAGE_BASE_DIR) = {IMAGE_BASE_DIR}")
print(f"    IMAGE_BASE_DIR 是否存在? {os.path.exists(IMAGE_BASE_DIR)}")

output_dir = os.path.join(IMAGE_BASE_DIR, "output_questions")
print(f"    output_questions 目录 = {output_dir}")
print(f"    output_questions 是否存在? {os.path.exists(output_dir)}")

# ── 2. 如果 output_questions 存在，列出里面的内容 ────────────
if os.path.exists(output_dir):
    print(f"\n[2] output_questions 目录内容：")
    items = os.listdir(output_dir)
    print(f"    共 {len(items)} 项：")
    for item in sorted(items):
        full = os.path.join(output_dir, item)
        if os.path.isdir(full):
            inner = os.listdir(full)
            print(f"    [DIR]  {item}/  ({len(inner)} 个文件)")
            for f in sorted(inner)[:5]:
                print(f"          - {f}")
            if len(inner) > 5:
                print(f"          ... (共 {len(inner)} 个)")
        else:
            print(f"    [FILE] {item}")
else:
    print(f"\n[2] output_questions 目录不存在！")
    print(f"    请检查是否运行过图片裁剪脚本")

# ── 3. 检查数据库里 questions 表有什么 ──────────────────────
print(f"\n[3] 数据库 questions 表：")
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM questions LIMIT 10").fetchall()
    total = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    print(f"    共有 {total} 条记录，打印前 10 条：")
    for i, r in enumerate(rows):
        print(f"    [{i+1}] topic_id={r['topic_id']}")
        print(f"           paper_name={r['paper_name']}")
        print(f"           question_number={r['question_number']}")
        print(f"           image_path={r['image_path']}")

        # 检查这个路径是否存在
        full_path = os.path.join(IMAGE_BASE_DIR, r['image_path'])
        exists = os.path.exists(full_path)
        print(f"           完整路径: {full_path}")
        print(f"           文件存在? {exists}")
    conn.close()
else:
    print("    数据库不存在")

# ── 4. 模拟 Flask 的 question_images 路由行为 ────────────────
print(f"\n[4] 模拟 Flask question_images 路由：")
print(f"    路由规则: /question_images/<path:filename>")
print(f"    send_from_directory('{IMAGE_BASE_DIR}', filename)")
print(f"    → 最终查找路径 = {IMAGE_BASE_DIR}/filename")

if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT image_path FROM questions LIMIT 1").fetchone()
    if row:
        filename = row['image_path']
        final = os.path.join(IMAGE_BASE_DIR, filename)
        print(f"\n    例如取第 1 条记录: filename = '{filename}'")
        print(f"    Flask 会查找: {final}")
        print(f"    文件存在? {os.path.exists(final)}")
    conn.close()

print("\n" + "=" * 70)
