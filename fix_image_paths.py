"""
一次性修复脚本：修正 questions 表中的 image_path（MySQL 版）
修复两个问题：
  1. 绝对路径 -> 相对路径 (output_questions/...)
  2. ENGAA_2016 -> ENGAA_2016_S1 (匹配磁盘上真实的目录名)
"""
import mysql.connector
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "webapp"))
from database.db_config import DB_CONFIG

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

print("=" * 70)
print("  修复 questions 表中的 image_path")
print("=" * 70)

# ── 1. 先确认磁盘上真实的子目录名 ────────────────────────────
output_dir = os.path.join(PROJECT_ROOT, "output_questions")
print(f"\n[1] 检查 output_questions 目录: {output_dir}")

subdirs = [d for d in os.listdir(output_dir)
           if os.path.isdir(os.path.join(output_dir, d))]
print(f"    找到 {len(subdirs)} 个子目录: {subdirs}")

real_dir = subdirs[0] if subdirs else None
print(f"    将使用的真实目录名: {real_dir}")

if real_dir is None:
    print("    ❌ 没有找到子目录！请先运行图片裁剪脚本。")
    sys.exit(1)

# ── 2. 连接数据库查看当前 image_path ─────────────────────────
print(f"\n[2] 当前数据库中的 image_path (前 5 条):")
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

cursor.execute("SELECT * FROM questions LIMIT 5")
rows = cursor.fetchall()
cursor.execute("SELECT COUNT(*) as cnt FROM questions")
total = cursor.fetchone()['cnt']
print(f"    questions 表共 {total} 条记录")
for r in rows:
    print(f"    topic_id={r['topic_id']}  paper={r['paper_name']}  q={r['question_number']}")
    print(f"      image_path = {r['image_path']}")

# ── 3. 分析路径 ──────────────────────────────────────────────
print(f"\n[3] 路径分析:")
sample = rows[0]['image_path']
print(f"    原始路径: {sample}")

is_absolute = sample.startswith("D:/") or sample.startswith("C:/") or sample.startswith("/")
print(f"    是否为绝对路径: {is_absolute}")

wrong_dir = "ENGAA_2016"
print(f"    当前写的目录名: {wrong_dir}")
print(f"    磁盘上的目录名: {real_dir}")
need_rename = wrong_dir in sample and wrong_dir != real_dir
print(f"    需要修正目录名: {need_rename}")

# ── 4. 执行修复 ──────────────────────────────────────────────
print(f"\n[4] 正在修复 image_path 字段...")

cursor.execute("SELECT DISTINCT paper_name FROM questions")
paper_names = [r['paper_name'] for r in cursor.fetchall()]
print(f"    paper_name 值: {paper_names}")

fixed_count = 0

cursor.execute("SELECT * FROM questions")
for q in cursor.fetchall():
    new_path = f"output_questions/{real_dir}/Question_{q['question_number']}.png"
    cursor.execute(
        "UPDATE questions SET image_path = %s WHERE id = %s",
        (new_path, q['id'])
    )
    fixed_count += 1

conn.commit()
print(f"    ✅ 已修正 {fixed_count} 条记录")

# ── 5. 验证修复结果 ──────────────────────────────────────────
print(f"\n[5] 验证修复后的路径是否能找到文件:")
ok_count = 0
fail_count = 0
cursor.execute("SELECT * FROM questions")
for q in cursor.fetchall():
    full_path = os.path.join(PROJECT_ROOT, q['image_path'])
    exists = os.path.exists(full_path)
    if exists:
        ok_count += 1
    else:
        fail_count += 1
        print(f"    ❌ 找不到: {full_path}")

print(f"\n    总结: {ok_count} 个文件存在，{fail_count} 个文件不存在")
conn.close()

if fail_count == 0:
    print("    ✅ 全部图片路径修复成功！")
else:
    print(f"    ⚠️  有 {fail_count} 个文件找不到，请检查。")

print("\n" + "=" * 70)
print("  完成！现在可以刷新网页查看图片了。")
print("  URL 示例: http://127.0.0.1:5000/topic/P1.1")
print("=" * 70)
