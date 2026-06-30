"""
数据库查询测试（MySQL 版）
==========================
测试 JOIN 查询是否正常工作。
语法差异：? → %s，但 SQL 语法本身不变。
"""
import mysql.connector
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "webapp"))
from database.db_config import DB_CONFIG

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

# 测试按 topic_id 查询
target_topic = "P1.2"
print(f"\n🔍 Searching for questions in Topic {target_topic}...\n")

cursor.execute('''
    SELECT syllabus.title, questions.question_number, questions.image_path 
    FROM questions
    JOIN syllabus ON questions.topic_id = syllabus.topic_id
    WHERE questions.topic_id = %s
''', (target_topic,))

results = cursor.fetchall()
if not results:
    print("No questions found for this topic.")
else:
    for row in results:
        print(f"[{row['title']}] -> Found Question {row['question_number']} located at: {row['image_path']}")


# 测试按 paper_name 查询
target_paper = "ENGAA_2018_S1"
print(f"\n🔍 Searching for questions in Paper {target_paper}...\n")

cursor.execute('''
    SELECT syllabus.title, questions.question_number, questions.image_path 
    FROM questions
    JOIN syllabus ON questions.topic_id = syllabus.topic_id
    WHERE questions.paper_name = %s
''', (target_paper,))

results = cursor.fetchall()
if not results:
    print("No questions found for this paper.")
else:
    for row in results:
        print(f"[{row['title']}] -> Found Question {row['question_number']} located at: {row['image_path']}")

conn.close()
