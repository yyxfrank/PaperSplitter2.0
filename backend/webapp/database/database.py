"""
MySQL 数据库访问层
==================
注意：与原 SQLite 版本相比，以下语法发生了变化：
  1. 占位符:  ? → %s
  2. 连接方式: sqlite3.connect(路径) → mysql.connector.connect(参数)
  3. 行工厂: sqlite3.Row → dictionary=True

表结构说明（Physics / Math 分表存储）：
  - syllabus_physics: topic_id (PK), title, objectives
  - syllabus_math:    topic_id (PK), chapter, objectives
  - questions_physics: id (PK), paper_name, question_number, topic_id (FK→syllabus_physics)
  - questions_math:    id (PK), paper_name, question_number, topic_id (FK→syllabus_math)
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


# ====================================================================
# 通用辅助函数
# ====================================================================

_TABLE_MAP = {
    "physics": {"syllabus": "syllabus_physics", "questions": "questions_physics"},
    "math":    {"syllabus": "syllabus_math",    "questions": "questions_math"},
}


def _syllabus_table(subject: str) -> str:
    """根据学科返回 syllabus 表名"""
    return _TABLE_MAP[subject]["syllabus"]


def _questions_table(subject: str) -> str:
    """根据学科返回 questions 表名"""
    return _TABLE_MAP[subject]["questions"]


# ====================================================================
# Syllabus 查询（分学科）
# ====================================================================

def _topic_sort_key(topic: dict) -> tuple:
    """将 topic_id 解析为可排序的元组，修复字符串排序 bug。

    字典序下 "M2.10" 会排在 "M2.2" 前面（因为 '1' < '2'）。
    将其转为 (字母, 章号, 节号) 三元组 → ('M', 2, 10) > ('M', 2, 2)，排序正确。

    格式: [字母前缀][章号].[节号]，如 "P1.1", "M2.10", "S3.5"
    """
    tid = topic["topic_id"]

    # 分离章号.节号
    parts = tid[1:].split(".")
    try:
        return (tid[0], int(parts[0]), int(parts[1]))
    except ValueError:
        pass

    # fallback：无法解析时按原始字符串排序
    return (tid, 0, 0)


def get_all_topics(subject: str, has_questions_only=False):
    """返回指定学科的所有 syllabus 主题，按 topic_id 的数值顺序排序。

    Args:
        subject: "physics" 或 "math"
        has_questions_only: 为 True 时只返回有题目的 topic。
    """
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        s_tbl = _syllabus_table(subject)
        q_tbl = _questions_table(subject)
        if has_questions_only:
            cursor.execute(f"""
                SELECT DISTINCT s.* FROM {s_tbl} s
                INNER JOIN {q_tbl} q ON s.topic_id = q.topic_id
                ORDER BY s.topic_id
            """)
        else:
            cursor.execute(f"SELECT * FROM {s_tbl} ORDER BY topic_id")
        topics = cursor.fetchall()
        # Python 层重新排序，修复字符串排序导致 M2.10 在 M2.2 前面的问题
        topics.sort(key=_topic_sort_key)
        return topics
    finally:
        conn.close()


def get_topic(subject: str, topic_id):
    """根据 topic_id 返回单个主题。"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            f"SELECT * FROM {_syllabus_table(subject)} WHERE topic_id = %s",
            (topic_id,),
        )
        topic = cursor.fetchone()
        return topic
    finally:
        conn.close()


def get_questions_by_topic(subject: str, topic_id):
    """返回匹配 topic_id 的所有题目，按试卷名和题号排序。"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            f"SELECT * FROM {_questions_table(subject)} WHERE topic_id = %s ORDER BY paper_name, question_number",
            (topic_id,),
        )
        questions = cursor.fetchall()
        return questions
    finally:
        conn.close()


def get_all_topics_grouped(subject: str, has_questions_only=False):
    """返回按父章节分组的话题（如 P1, P2, M1...）。

    现在 physics 和 math 都使用 chapter 字段作为分组键。
    """
    topics = get_all_topics(subject, has_questions_only)
    if topics is None:
        return None

    grouped = {}
    for topic in topics:
        # 两个学科都用 chapter 字段分组
        prefix = topic["chapter"]
        if prefix not in grouped:
            grouped[prefix] = []
        grouped[prefix].append(dict(topic))

    return grouped


# ====================================================================
# 搜索（分学科）
# ====================================================================

def search_topics(subject: str, keyword: str):
    """
    在指定学科的 syllabus 中搜索关键词。
    - physics: 在 title 和 objectives 中搜索
    - math: 在 chapter 和 objectives 中搜索
    """
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        s_tbl = _syllabus_table(subject)
        if subject == "math":
            cursor.execute(
                f"SELECT * FROM {s_tbl} WHERE chapter LIKE %s OR objectives LIKE %s",
                (f"%{keyword}%", f"%{keyword}%"),
            )
        else:
            cursor.execute(
                f"SELECT * FROM {s_tbl} WHERE title LIKE %s OR objectives LIKE %s",
                (f"%{keyword}%", f"%{keyword}%"),
            )
        topics = cursor.fetchall()
        return topics
    finally:
        conn.close()


# ====================================================================
# 兼容旧版 API（单一 syllabus/questions 表）
# 以下函数保持原名，用于旧模板路由
# ====================================================================

def _get_all_topics_old(has_questions_only=False):
    """兼容：旧版 syllabus 表查询"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        if has_questions_only:
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


def get_all_topics_grouped_old(has_questions_only=False):
    """兼容：旧版分组查询"""
    topics = _get_all_topics_old(has_questions_only)
    if topics is None:
        return None
    grouped = {}
    for topic in topics:
        tid = topic["topic_id"]
        prefix = ".".join(tid.split(".")[:-1]) if "." in tid else tid
        if prefix not in grouped:
            grouped[prefix] = []
        grouped[prefix].append(dict(topic))
    return grouped


def get_topic_old(topic_id):
    """兼容：旧版单一 topic 查询"""
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


def get_questions_by_topic_old(topic_id):
    """兼容：旧版题目查询"""
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


def search_topics_old(keyword):
    """兼容：旧版搜索"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM syllabus WHERE title LIKE %s OR objectives LIKE %s",
            (f"%{keyword}%", f"%{keyword}%"),
        )
        topics = cursor.fetchall()
        return topics
    finally:
        conn.close()
