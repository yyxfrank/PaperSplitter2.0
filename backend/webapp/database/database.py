"""
MySQL 数据库访问层
==================
注意：与原 SQLite 版本相比，以下语法发生了变化：
  1. 占位符:  ? → %s
  2. 连接方式: sqlite3.connect(路径) → mysql.connector.connect(参数)
  3. 行工厂: sqlite3.Row → dictionary=True
"""
import os
import mysql.connector
from mysql.connector import Error as MySQLError

# 项目根目录（用于 IMAGE_BASE_DIR，路径逻辑不变）
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

# 导入 MySQL 连接配置
from .db_config import DB_CONFIG

IMAGE_BASE_DIR = _PROJECT_ROOT


def get_db_connection():
    """
    获取 MySQL 数据库连接。

    注意：不要在这里设置 dictionary=True！
    它是 cursor() 的参数，不是 connect() 的参数。

    与原 SQLite 版本的区别：
      - SQLite: sqlite3.connect(DB_PATH) + row_factory = sqlite3.Row
      - MySQL:  mysql.connector.connect(host=..., user=..., database=...)
                + 每个 cursor: conn.cursor(dictionary=True)
    """
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            charset=DB_CONFIG["charset"],
            collation=DB_CONFIG["collation"],
            use_pure=DB_CONFIG["use_pure"],
        )
        return conn
    except MySQLError as e:
        print(f"[database.py] MySQL 连接失败: {e}")
        return None


def get_all_topics(has_questions_only=False):
    """返回所有 syllabus 主题，按 topic_id 排序。

    Args:
        has_questions_only: 为 True 时只返回有题目的 topic（INNER JOIN questions 表）。
    """
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        # dictionary=True 使 cursor 返回字典行（等价于 SQLite 的 row_factory = sqlite3.Row）
        cursor = conn.cursor(dictionary=True)
        if has_questions_only:
            # INNER JOIN = 只返回 questions 表中存在的 topic_id
            # DISTINCT 防止同一个 topic 有多道题时重复
            cursor.execute("""
                SELECT DISTINCT s.* FROM syllabus s
                INNER JOIN questions q ON s.topic_id = q.topic_id
                ORDER BY s.topic_id
            """)
        else:
            cursor.execute("SELECT * FROM syllabus ORDER BY topic_id")
        topics = cursor.fetchall()
        return topics
    finally:
        conn.close()


def get_topic(topic_id):
    """根据 topic_id 返回单个主题。"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM syllabus WHERE topic_id = %s",
            (topic_id,),
        )
        topic = cursor.fetchone()
        return topic
    finally:
        conn.close()


def get_questions_by_topic(topic_id):
    """
    返回匹配 topic_id 的所有题目，按试卷名和题号排序。

    索引优化说明：
      - 此查询的 WHERE topic_id = ? 条件每天被高频调用
      - 如果在 questions 表上没有 topic_id 索引，MySQL 会做全表扫描
      - 建表语句中已为 topic_id 添加索引 idx_topic_id
    """
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM questions WHERE topic_id = %s ORDER BY paper_name, question_number",
            (topic_id,),
        )
        questions = cursor.fetchall()
        return questions
    finally:
        conn.close()


def get_all_papers():
    """返回数据库中所有不重复的试卷名。"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT DISTINCT paper_name FROM questions ORDER BY paper_name"
        )
        papers = cursor.fetchall()
        # 返回纯字符串列表（兼容原有 API）
        return [p["paper_name"] for p in papers]
    finally:
        conn.close()


def get_all_topics_grouped(has_questions_only=False):
    """返回按父章节分组的话题（如 P1, P2, M1...）。

    Args:
        has_questions_only: 为 True 时只保留有题目的 topic。
    """
    topics = get_all_topics(has_questions_only)
    if topics is None:
        return None

    grouped = {}
    for topic in topics:
        tid = topic["topic_id"]
        # 提取章节前缀: 如 "P1.1" → "P1"
        prefix = ".".join(tid.split(".")[:-1]) if "." in tid else tid
        if prefix not in grouped:
            grouped[prefix] = []
        grouped[prefix].append(dict(topic))

    return grouped


def search_topics(keyword):
    """
    在 syllabus 的 title 和 objectives 中搜索关键词。

    防止 SQL 注入的说明：
      - 使用 %s 占位符（参数化查询），数据库驱动会自动转义特殊字符
      - 关键词中的单引号、反斜杠等不会被解释为 SQL 语法
      - 永远不要用 f"LIKE '%{keyword}%'" 这种字符串拼接方式
    """
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        # %s 是安全的占位符，keyword 值中的特殊字符会被自动转义
        cursor.execute(
            "SELECT * FROM syllabus WHERE title LIKE %s OR objectives LIKE %s",
            (f"%{keyword}%", f"%{keyword}%"),
        )
        topics = cursor.fetchall()
        return topics
    finally:
        conn.close()
