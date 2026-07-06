"""
数据库构建工具（MySQL 版）
========================
与原 SQLite 版本的关键语法差异：
  1. 占位符: ? → %s
  2. AUTOINCREMENT → AUTO_INCREMENT
  3. INSERT OR IGNORE → INSERT IGNORE
  4. ON CONFLICT ... DO UPDATE → ON DUPLICATE KEY UPDATE
  5. 连接方式: sqlite3.connect(路径) → mysql.connector.connect(参数)
"""
import json
import os
import mysql.connector
from mysql.connector import Error as MySQLError

# 导入 MySQL 连接配置
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "webapp"))
from database.db_config import DB_CONFIG


def append_to_database(paper_name, syllabus_json, classified_json, image_folder, db_name=None):
    """
    将 AI 分类结果写入 MySQL 数据库。

    参数:
      paper_name:      试卷名称（如 "ENGAA_2016_S1"）
      syllabus_json:   大纲 JSON 文件路径
      classified_json: AI 分类结果 JSON 文件路径
      image_folder:    图片存放目录（如 "output_questions"）
      db_name:         兼容原接口保留，MySQL 版不使用此参数
    """
    print(f"Connecting to MySQL database: {DB_CONFIG['database']}...")

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
    except MySQLError as e:
        print(f"❌ MySQL 连接失败: {e}")
        print("   请确保 MySQL 服务已启动，并且在 db_config.py 中配置了正确的连接参数。")
        return

    cursor = conn.cursor()

    # ── 创建表结构（首次运行自动创建）────────────────────────────
    # 外键（FOREIGN KEY）的作用：
    #   保证 questions.topic_id 的值必须在 syllabus.topic_id 中存在
    #   如果尝试插入不存在的 topic_id，MySQL 会拒绝操作
    #   这防止了"孤儿数据"——即题目引用了不存在的教学大纲主题

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS syllabus (
            topic_id    VARCHAR(50)  NOT NULL  COMMENT '主题编号，如 P1.1、M2.3',
            title       VARCHAR(500) NOT NULL  COMMENT '主题标题',
            objectives  TEXT                   COMMENT '学习目标（大段文本）',
            PRIMARY KEY (topic_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id              INT           NOT NULL  AUTO_INCREMENT  COMMENT '自增主键',
            paper_name      VARCHAR(100)  NOT NULL                   COMMENT '试卷名称',
            question_number INT           NOT NULL                   COMMENT '题号',
            topic_id        VARCHAR(50)   NOT NULL                   COMMENT '所属主题编号',
            image_path      VARCHAR(500)                             COMMENT '题目图片路径',
            PRIMARY KEY (id),
            UNIQUE KEY uk_paper_question (paper_name, question_number)
                COMMENT '同一试卷内题号唯一',
            INDEX idx_topic_id (topic_id)
                COMMENT '加速按 topic_id 查询题目的速度',
            CONSTRAINT fk_questions_topic
                FOREIGN KEY (topic_id) REFERENCES syllabus (topic_id)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # ── 插入大纲数据 ────────────────────────────────────────────
    print("Syncing Syllabus...")
    with open(syllabus_json, 'r', encoding='utf-8') as f:
        syllabus_data = json.load(f)
        for chapter in syllabus_data:
            # INSERT IGNORE（SQLite 的 INSERT OR IGNORE）：
            # 如果 topic_id 已存在，则跳过，不会报错
            cursor.execute("""
                INSERT IGNORE INTO syllabus (topic_id, title, objectives)
                VALUES (%s, %s, %s)
            """, (chapter['id'], chapter['title'], chapter['objectives']))

    # ── 插入新题目 ──────────────────────────────────────────────
    print(f"Adding questions from {paper_name}...")
    with open(classified_json, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)

        added_count = 0

        for q in questions_data:
            q_num = q['question_number']
            t_id = q['topic_id']

            # 构造图片路径: output_questions/ENGAA_2016_S1/Question_1.png
            img_path = os.path.join(image_folder, paper_name, f"Question_{q_num}.png")
            img_path = img_path.replace("\\", "/")

            # ON DUPLICATE KEY UPDATE（MySQL 的 UPSERT 语法）：
            # 与 SQLite 的 "ON CONFLICT(paper_name, question_number) DO UPDATE" 等效
            # 如果同一试卷同一题号已存在，则更新 image_path 和 topic_id
            cursor.execute("""
                INSERT INTO questions (paper_name, question_number, topic_id, image_path)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    image_path = VALUES(image_path),
                    topic_id = VALUES(topic_id)
            """, (paper_name, q_num, t_id, img_path))

            added_count += 1

    conn.commit()
    conn.close()
    print(f"✅ Successfully appended {added_count} questions from {paper_name} into MySQL database!")


# ==========================================
# 运行数据库写入器
# ==========================================
if __name__ == "__main__":
    PAPER_IDENTIFIER = "ENGAA_2017_S1"
    SYLLABUS_FILE = "structured_syllabus_math_1.json"
    CLASSIFIED_FILE = "classified_questions_math_1.json"
    IMAGE_DIR = "output_questions"

    append_to_database(PAPER_IDENTIFIER, SYLLABUS_FILE, CLASSIFIED_FILE, IMAGE_DIR)
