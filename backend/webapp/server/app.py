import os
import sys
from flask import Flask, render_template, abort, send_from_directory, request, jsonify
from flask_cors import CORS

# Add parent dirs so we can import the database module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.database import (
    get_all_topics,
    get_all_topics_grouped,
    get_topic,
    get_questions_by_topic,
    search_topics,
    # 旧版兼容函数
    get_all_topics_grouped_old,
    get_topic_old,
    get_questions_by_topic_old,
    search_topics_old,
    IMAGE_BASE_DIR,
)

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
)

# 允许来自任何来源的跨域请求（开发阶段用）
CORS(app)


# ================================================================
# 原有路由（保留不动）—— 给原生的 Jinja2 页面用
# ================================================================

@app.route("/")
def syllabus():
    grouped = get_all_topics_grouped_old()
    flat = None  # old templates don't use flat

    if grouped is None:
        return render_template("index.html", grouped=None, topics=None)

    return render_template("index.html", grouped=grouped, topics=flat)


@app.route("/topic/<topic_id>")
def topic_detail(topic_id):
    topic = get_topic_old(topic_id)
    if topic is None:
        abort(404, description=f"Topic '{topic_id}' not found.")

    questions = get_questions_by_topic_old(topic_id)
    if questions is None:
        questions = []

    questions_by_paper = {}
    for q in questions:
        paper = q["paper_name"]
        if paper not in questions_by_paper:
            questions_by_paper[paper] = []
        questions_by_paper[paper].append(q)

    return render_template(
        "topic.html",
        topic=topic,
        questions=questions,
        questions_by_paper=questions_by_paper,
    )


@app.route("/question_images/<path:filename>")
def question_images(filename):
    if not os.path.exists(IMAGE_BASE_DIR):
        abort(404, "No question images found. Run the extraction pipeline first.")
    return send_from_directory(IMAGE_BASE_DIR, filename)


@app.route("/search")
def search():
    keyword = request.args.get("q", "").strip()
    topics = None
    if keyword:
        topics = search_topics_old(keyword)
    return render_template("search.html", topics=topics, keyword=keyword)


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html", error_msg=error.description), 404


# ================================================================
# JSON API 路由 —— 给 Vue 前端调用的接口
# 所有新 API 都以 /api/subject/<subject>/ 开头，
# <subject> 取值为 physics 或 math
# ================================================================

def _validate_subject(subject):
    """校验学科参数，返回 (是否合法, 错误响应)"""
    if subject not in ("physics", "math"):
        return False, jsonify({"code": 1, "message": f"Invalid subject: {subject}", "data": None})
    return True, None


@app.route("/api/subject/<subject>/topics")
def api_topics(subject):
    """获取指定学科的所有 syllabus 主题（扁平列表）"""
    valid, err = _validate_subject(subject)
    if not valid:
        return err
    has_questions = request.args.get("has_questions", "").lower() in ("1", "true")
    topics = get_all_topics(subject, has_questions_only=has_questions)
    if topics is None:
        return jsonify({"code": 1, "message": "数据库连接失败", "data": None})
    return jsonify({"code": 0, "data": topics})


@app.route("/api/subject/<subject>/topics/grouped")
def api_topics_grouped(subject):
    """获取指定学科按前缀分组后的 syllabus"""
    valid, err = _validate_subject(subject)
    if not valid:
        return err
    has_questions = request.args.get("has_questions", "").lower() in ("1", "true")
    grouped = get_all_topics_grouped(subject, has_questions_only=has_questions)
    if grouped is None:
        return jsonify({"code": 1, "message": "数据库连接失败", "data": None})
    return jsonify({"code": 0, "data": grouped})


@app.route("/api/subject/<subject>/topics/<topic_id>")
def api_topic_detail(subject, topic_id):
    """获取指定学科某个 topic 的详细信息 + 所有题目"""
    valid, err = _validate_subject(subject)
    if not valid:
        return err
    topic = get_topic(subject, topic_id)
    if topic is None:
        return jsonify({
            "code": 1,
            "message": f"Topic '{topic_id}' not found in {subject}",
            "data": None
        }), 404

    questions = get_questions_by_topic(subject, topic_id) or []

    # 按试卷名分组
    questions_by_paper = {}
    for q in questions:
        paper = q["paper_name"]
        if paper not in questions_by_paper:
            questions_by_paper[paper] = []
        questions_by_paper[paper].append(q)

    return jsonify({
        "code": 0,
        "data": {
            "topic": topic,
            "questions": questions,
            "questions_by_paper": questions_by_paper
        }
    })


@app.route("/api/subject/<subject>/search")
def api_search(subject):
    """按关键词在指定学科的 syllabus 中搜索"""
    valid, err = _validate_subject(subject)
    if not valid:
        return err
    keyword = request.args.get("q", "").strip()
    if not keyword:
        return jsonify({"code": 0, "data": []})

    topics = search_topics(subject, keyword)
    if topics is None:
        return jsonify({"code": 1, "message": "数据库连接失败", "data": None})

    return jsonify({"code": 0, "data": topics})


@app.route("/api/question_images/<path:filename>")
def api_question_images(filename):
    """提供题目图片给 Vue 前端"""
    if not os.path.exists(IMAGE_BASE_DIR):
        return jsonify({"code": 1, "message": "图片目录不存在", "data": None}), 404
    return send_from_directory(IMAGE_BASE_DIR, filename)


# ----------------------------------------------------------------
# Launch
# ----------------------------------------------------------------
if __name__ == "__main__":
    print(f"Starting PaperSplitter Web App...")
    print(f"Database: {os.path.join(os.path.dirname(__file__), '..', '..', '..', 'master_exam_data.db')}")
    print(f"Image dir: {IMAGE_BASE_DIR}")
    print(f"Open http://127.0.0.1:5000 in your browser.\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
