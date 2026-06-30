"""
搜索功能调试脚本（MySQL 版）
============================

⚠️  重要：SQL 注入防范说明
---------------------------
原 SQLite 版本第 53 行使用了字符串拼接：
    sql = f"SELECT * FROM syllabus WHERE title LIKE '%{kw}%'"

这是典型的 SQL 注入漏洞，原因：
  - 如果 kw = "' OR 1=1 --"，拼接后的 SQL 变成：
    SELECT * FROM syllabus WHERE title LIKE '%' OR 1=1 --%'
  - 这会返回所有行，因为 1=1 永远为真
  - 更严重：如果 kw = "'; DROP TABLE syllabus; --"，会直接删除表

正确做法（已在下方修复）：
  - 使用 %s 占位符（参数化查询）
  - 数据库驱动会自动处理转义，kw 中的特殊字符不会被当成 SQL 语法执行
"""
import mysql.connector
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "webapp"))
from database.db_config import DB_CONFIG, _PROJECT_ROOT
from database.database import search_topics, get_all_topics

print("=" * 70)
print("  PaperSplitter 搜索功能调试 (MySQL)")
print("=" * 70)

# ── 1. 检查数据库连接 ──────────────────────────────────────────
print(f"\n[1] 数据库配置: {DB_CONFIG['database']}@{DB_CONFIG['host']}")

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    conn.ping()  # 验证连接有效
    print("    连接成功 ✓")
except Exception as e:
    print(f"    ❌ 数据库连接失败: {e}")
    print("    请确保 MySQL 服务已启动且 db_config.py 配置正确。")
    sys.exit(1)

# ── 2. 打印 syllabus 表 ────────────────────────────────────────
cursor.execute("SELECT * FROM syllabus ORDER BY topic_id")
rows = cursor.fetchall()

print(f"\n[2] syllabus 表共有 {len(rows)} 条记录：")
for i, r in enumerate(rows):
    print(f"    [{i+1}] id={r['topic_id']:<8} title={r['title']}")
    obj = r['objectives'][:80] + "..." if len(r['objectives']) > 80 else r['objectives']
    print(f"           objectives: {obj}")

# ── 3. 测试 search_topics 函数 ──────────────────────────────────
print(f"\n[3] 用 search_topics() 函数实际查询：")

test_keywords = []
for r in rows:
    test_keywords.append(r['title'][:2])
    if len(test_keywords) >= 3:
        break
test_keywords.extend(["力学", "运动", "微积分"])

for kw in test_keywords:
    result = search_topics(kw)
    if result is None:
        print(f"    '{kw}' → 返回 None (数据库连接失败)")
    else:
        print(f"    '{kw}' → 匹配 {len(result)} 条")
        for r in result:
            print(f"        ✓ {r['topic_id']} {r['title']}")

# ── 4. 手动执行 SQL（使用参数化查询，防注入）─────────────────────
print(f"\n[4] 手动执行 SQL，观察 LIKE 行为（参数化查询）：")
for kw in test_keywords:
    # ✅ 正确做法：使用 %s 占位符
    # ❌ 错误做法：f"SELECT * FROM syllabus WHERE title LIKE '%{kw}%'"
    cursor.execute(
        "SELECT * FROM syllabus WHERE title LIKE %s OR objectives LIKE %s",
        (f"%{kw}%", f"%{kw}%")
    )
    manual = cursor.fetchall()
    print(f"    SQL: SELECT * FROM syllabus WHERE title LIKE %s OR objectives LIKE %s")
    print(f"    参数: ('%{kw}%', '%{kw}%')")
    print(f"    → 返回 {len(manual)} 条")

# ── 5. 检查大小写敏感性 ────────────────────────────────────────
# MySQL 的 utf8mb4_unicode_ci 是大小写不敏感的（ci = case insensitive）
print(f"\n[5] 检查 SQL LIKE 大小写敏感性：")
print("    MySQL utf8mb4_unicode_ci 默认大小写不敏感")
for r in rows[:3]:
    title = r['title']
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM syllabus WHERE title LIKE %s",
        (f"%{title}%",)
    )
    count = cursor.fetchone()['cnt']
    print(f"    '{title}': 匹配 {count} 条")

conn.close()

print("\n" + "=" * 70)
