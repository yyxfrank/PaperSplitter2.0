"""
从 MySQL 删除指定试卷的题目
============================
语法差异说明：
  - SQLite:  DELETE FROM questions WHERE paper_name='值'
  - MySQL:   DELETE FROM questions WHERE paper_name = '值'  (语法相同)
  - 注意：MySQL 字符串也支持单引号，但建议用参数化查询防注入
"""
import mysql.connector
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "webapp"))
from database.db_config import DB_CONFIG

conn = mysql.connector.connect(**DB_CONFIG)
cur = conn.cursor()

# 使用 %s 占位符（SQLite 用 ?），防止 SQL 注入
paper_to_delete = "ENGAA_2016_S1"
cur.execute("DELETE FROM questions WHERE paper_name = %s", (paper_to_delete,))

conn.commit()
conn.close()
print(f"Deleted questions for {paper_to_delete}")
