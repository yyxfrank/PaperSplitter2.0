"""
SQLite → MySQL 数据迁移脚本
============================
从旧的 SQLite 数据库读取数据，写入 MySQL。

用法：
  1. 先在 MySQL 中创建 exam_system 数据库（或修改 db_config.py 中的 database 名称）
  2. 确保 master_exam_data.db 文件存在（旧 SQLite 数据库）
  3. 运行本脚本: python backend/offline/loaders/sql_exchange.py

注意：
  - 密码统一配置在 backend/webapp/database/db_config.py 中
  - 不要在本文件中硬编码密码
"""
import sqlite3
import os
import sys

# 导入 MySQL 连接配置，避免密码硬编码
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "webapp"))
from database.db_config import DB_CONFIG
import mysql.connector

# 连接 SQLite（旧库）
SQLITE_DB = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "master_exam_data.db"
)
if not os.path.exists(SQLITE_DB):
    print(f"❌ 找不到 SQLite 数据库文件: {SQLITE_DB}")
    print("   请确认 master_exam_data.db 文件路径正确。")
    sys.exit(1)

sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_conn.row_factory = sqlite3.Row

# 连接 MySQL（新库）
print(f"正在连接 MySQL: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
mysql_conn = mysql.connector.connect(
    host=DB_CONFIG["host"],
    user=DB_CONFIG["user"],
    password=DB_CONFIG["password"],
    database=DB_CONFIG["database"],
    charset=DB_CONFIG["charset"],
    collation=DB_CONFIG["collation"],
)
mysql_cursor = mysql_conn.cursor()

# 检查 syllabus 表是否有数据
sqlite_rows = sqlite_conn.execute("SELECT COUNT(*) FROM syllabus").fetchone()[0]
print(f"SQLite syllabus 表: {sqlite_rows} 条记录")

# 迁移 syllabus
rows = sqlite_conn.execute("SELECT * FROM syllabus").fetchall()
for r in rows:
    mysql_cursor.execute(
        "INSERT INTO syllabus (topic_id, title, objectives) VALUES (%s, %s, %s) "
        "ON CONFLICT DO UPDATE SET title = EXCLUDED.title, objectives = EXCLUDED.objectives",
        (r["topic_id"], r["title"], r["objectives"])
    )
mysql_conn.commit()
print(f"✅ 已迁移 {len(rows)} 条 syllabus 记录")

# 检查 questions 表是否有数据
sqlite_rows = sqlite_conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
print(f"SQLite questions 表: {sqlite_rows} 条记录")

# 迁移 questions
rows = sqlite_conn.execute("SELECT * FROM questions").fetchall()
for r in rows:
    mysql_cursor.execute(
        "INSERT INTO questions (paper_name, question_number, topic_id, image_path) "
        "VALUES (%s, %s, %s, %s)",
        (r["paper_name"], r["question_number"], r["topic_id"], r["image_path"])
    )

mysql_conn.commit()
mysql_cursor.close()
mysql_conn.close()
sqlite_conn.close()
print(f"✅ 已迁移 {len(rows)} 条 questions 记录")
print("🎉 迁移完成！")
