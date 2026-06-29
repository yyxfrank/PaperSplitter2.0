import sqlite3
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "webapp"))
from database.database import DB_PATH, get_db_connection, search_topics, get_all_topics

print("=" * 70)
print("  PaperSplitter 搜索功能调试")
print("=" * 70)

# ── 1. 检查数据库文件 ─────────────────────────────────────────
print(f"\n[1] 数据库路径: {DB_PATH}")
print(f"    文件存在? {os.path.exists(DB_PATH)}")

if not os.path.exists(DB_PATH):
    print("    ❌ 数据库文件不存在！请先运行 build_database.py")
    sys.exit(1)

# ── 2. 打印 syllabus 表里所有行 ────────────────────────────────
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT * FROM syllabus ORDER BY topic_id").fetchall()

print(f"\n[2] syllabus 表共有 {len(rows)} 条记录：")
for i, r in enumerate(rows):
    print(f"    [{i+1}] id={r['topic_id']:<8} title={r['title']}")
    obj = r['objectives'][:80] + "..." if len(r['objectives']) > 80 else r['objectives']
    print(f"           objectives: {obj}")

# ── 3. 用 search_topics 函数实际查几个关键字 ───────────────────
print(f"\n[3] 用 search_topics() 函数实际查询：")

test_keywords = []
for r in rows:
    test_keywords.append(r['title'][:2])   # 取每个章节标题前两个字
    if len(test_keywords) >= 3:
        break
test_keywords.extend(["力学", "运动", "微积分"])   # 加几个常见词

for kw in test_keywords:
    result = search_topics(kw)
    if result is None:
        print(f"    '{kw}' → 返回 None (数据库连接失败)")
    else:
        print(f"    '{kw}' → 匹配 {len(result)} 条")
        for r in result:
            print(f"        ✓ {r['topic_id']} {r['title']}")

# ── 4. 手动执行 SQL，验证 LIKE 语法 ─────────────────────────────
print(f"\n[4] 手动执行 SQL，观察 LIKE 行为：")
for kw in test_keywords:
    sql = f"SELECT * FROM syllabus WHERE title LIKE '%{kw}%' OR objectives LIKE '%{kw}%'"
    manual = conn.execute(sql).fetchall()
    print(f"    SQL: {sql}")
    print(f"    → 返回 {len(manual)} 条")

# ── 5. 检查大小写敏感性 ────────────────────────────────────────
print(f"\n[5] 检查 SQL LIKE 大小写敏感性：")
for r in rows[:3]:
    title = r['title']
    upper_title = title.upper()
    lower_title = title.lower()
    count_upper = conn.execute(
        "SELECT COUNT(*) FROM syllabus WHERE title LIKE ?",
        (f"%{upper_title}%",)
    ).fetchone()[0]
    count_lower = conn.execute(
        "SELECT COUNT(*) FROM syllabus WHERE title LIKE ?",
        (f"%{lower_title}%",)
    ).fetchone()[0]
    count_exact = conn.execute(
        "SELECT COUNT(*) FROM syllabus WHERE title LIKE ?",
        (f"%{title}%",)
    ).fetchone()[0]
    print(f"    '{title}': 大写匹配={count_upper}, 小写匹配={count_lower}, 原文匹配={count_exact}")

conn.close()

# ── 6. 检查 app.py 传给模板的变量名 vs 模板里用的变量名 ────────
print(f"\n[6] 变量名一致性检查（app.py vs search.html）：")
print("    app.py search() 函数传给 render_template 的变量名:")
print("        ???=???  (需要看 app.py 实际代码)")
print("    search.html 模板里引用的变量名:")
print("        results, results|length, for topic in results")
print("    ⚠️ 如果两边不一致，模板里永远拿不到数据！")

print("\n" + "=" * 70)
