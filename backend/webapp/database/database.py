import sqlite3
import os

# Project root: go up from backend/webapp/database/ to project root
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

DB_PATH = os.path.join(_PROJECT_ROOT, "master_exam_data.db")
IMAGE_BASE_DIR = _PROJECT_ROOT  # send_from_directory will receive the full relative path including "output_questions/..."


def get_db_connection():
    """Get a connection to the master exam database with row factory enabled."""
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_topics():
    """Return all syllabus topics ordered by topic_id."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        topics = conn.execute(
            "SELECT * FROM syllabus ORDER BY topic_id"
        ).fetchall()
        return topics
    finally:
        conn.close()


def get_topic(topic_id):
    """Return a single topic by topic_id."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        topic = conn.execute(
            "SELECT * FROM syllabus WHERE topic_id = ?", (topic_id,)
        ).fetchone()
        return topic
    finally:
        conn.close()


def get_questions_by_topic(topic_id):
    """Return all questions matching the given topic_id, ordered by paper then question number."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        questions = conn.execute(
            "SELECT * FROM questions WHERE topic_id = ? ORDER BY paper_name, question_number",
            (topic_id,),
        ).fetchall()
        return questions
    finally:
        conn.close()


def get_all_papers():
    """Return the list of distinct paper names in the database."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        papers = conn.execute(
            "SELECT DISTINCT paper_name FROM questions ORDER BY paper_name"
        ).fetchall()
        return [p["paper_name"] for p in papers]
    finally:
        conn.close()


def get_all_topics_grouped():
    """Return topics grouped by parent chapter (e.g., P1, P2, M1...)."""
    topics = get_all_topics()
    if topics is None:
        return None

    grouped = {}
    for topic in topics:
        tid = topic["topic_id"]
        # Extract chapter prefix: e.g., "P1" from "P1.1"
        prefix = ".".join(tid.split(".")[:-1]) if "." in tid else tid
        if prefix not in grouped:
            grouped[prefix] = []
        grouped[prefix].append(dict(topic))

    return grouped

def search_topics(keyword):
    """Return topics matching the given keyword in title or objectives."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        topics = conn.execute(
            "SELECT * FROM syllabus WHERE title LIKE ? OR objectives LIKE ?",
            (f"%{keyword}%", f"%{keyword}%"),
        ).fetchall()
        return topics
    finally:
        conn.close()