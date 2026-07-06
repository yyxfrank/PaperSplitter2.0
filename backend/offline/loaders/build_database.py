"""
数据库构建工具（MySQL 版）
========================
支持 Physics / Math 分表存储。

表结构：
  - syllabus_physics: topic_id (PK), chapter, title, objectives
  - syllabus_math:    topic_id (PK), chapter, objectives
  - questions_physics: id (PK), paper_name, question_number, topic_id (FK→syllabus_physics)
  - questions_math:    id (PK), paper_name, question_number, topic_id (FK→syllabus_math)
"""
import json
import os
import mysql.connector
from mysql.connector import Error as MySQLError

# 导入 MySQL 连接配置
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "webapp"))
from database.db_config import DB_CONFIG


def create_tables(cursor, subject):
    """为指定学科创建 syllabus 和 questions 表。

    支持 subject="physics" 或 "math"。
    """
    s_tbl = f"syllabus_{subject}"
    q_tbl = f"questions_{subject}"

    if subject == "math":
        # Math syllabus: 没有 title, 有 chapter 字段
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {s_tbl} (
                topic_id    VARCHAR(50)  NOT NULL  COMMENT '主题编号，如 M1.1、M2.3',
                chapter     VARCHAR(50)  NOT NULL  COMMENT '章节名称，如 M1、M2',
                objectives  TEXT                   COMMENT '学习目标（大段文本）',
                PRIMARY KEY (topic_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
    else:
        # Physics syllabus: 有 title 和 chapter 字段
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {s_tbl} (
                topic_id    VARCHAR(50)  NOT NULL  COMMENT '主题编号，如 P1.1、S1.2',
                chapter     VARCHAR(50)  NOT NULL  COMMENT '章节名称，如 P1、P2、S1',
                title       VARCHAR(500) NOT NULL  COMMENT '主题标题',
                objectives  TEXT                   COMMENT '学习目标（大段文本）',
                PRIMARY KEY (topic_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {q_tbl} (
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
            CONSTRAINT fk_{q_tbl}_topic
                FOREIGN KEY (topic_id) REFERENCES {s_tbl} (topic_id)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)


def append_to_database(paper_name, syllabus_json, classified_json, image_folder,
                       db_name=None, subject="physics"):
    """
    将 AI 分类结果写入 MySQL 数据库（按学科分表）。

    参数:
      paper_name:      试卷名称（如 "ENGAA_2016_S1"）
      syllabus_json:   大纲 JSON 文件路径
      classified_json: AI 分类结果 JSON 文件路径
      image_folder:    图片存放目录（如 "output_questions"）
      db_name:         兼容原接口保留，MySQL 版不使用此参数
      subject:         学科，取值为 "physics" 或 "math"
    """
    print(f"Connecting to MySQL database: {DB_CONFIG['database']}...")
    print(f"Subject: {subject}")

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

    # ── 创建表结构（根据学科）─────────────────────────────────────
    create_tables(cursor, subject)

    s_tbl = f"syllabus_{subject}"

    # ── 插入大纲数据 ────────────────────────────────────────────
    print("Syncing Syllabus...")
    with open(syllabus_json, 'r', encoding='utf-8') as f:
        syllabus_data = json.load(f)
        for syllabus in syllabus_data:
            if subject == "math":
                # Math: 没有 title，有 chapter 字段
                cursor.execute(f"""
                    INSERT INTO {s_tbl} (topic_id, chapter, objectives)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        chapter = VALUES(chapter),
                        objectives = VALUES(objectives)
                """, (syllabus['id'], syllabus['chapter'], syllabus['objectives']))
            else:
                # Physics: 有 title 和 chapter
                cursor.execute(f"""
                    INSERT INTO {s_tbl} (topic_id, chapter, title, objectives)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        chapter = VALUES(chapter),
                        title = VALUES(title),
                        objectives = VALUES(objectives)
                """, (syllabus['id'], syllabus['chapter'], syllabus['title'], syllabus['objectives']))

    # ── 插入新题目 ──────────────────────────────────────────────
    q_tbl = f"questions_{subject}"
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

            cursor.execute(f"""
                INSERT INTO {q_tbl} (paper_name, question_number, topic_id, image_path)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    image_path = VALUES(image_path),
                    topic_id = VALUES(topic_id)
            """, (paper_name, q_num, t_id, img_path))

            added_count += 1

    conn.commit()
    conn.close()
    print(f"✅ Successfully appended {added_count} questions from {paper_name} into MySQL database ({subject})!")


# ==========================================
# 运行数据库写入器
# ==========================================
if __name__ == "__main__":
    PAPER_IDENTIFIER = "ENGAA_2023_S1"
    SYLLABUS_FILE = "structured_syllabus_physics.json"
    CLASSIFIED_FILE = "classified_questions_physics.json"
    IMAGE_DIR = "output_questions"

    append_to_database(
        PAPER_IDENTIFIER,
        SYLLABUS_FILE,
        CLASSIFIED_FILE,
        IMAGE_DIR,
        subject="physics"  # 指定为 math 学科
    )
