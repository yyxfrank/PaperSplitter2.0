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
    IMAGE_BASE_DIR,
)

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
)

# 允许来自任何来源的跨域请求（开发阶段用）
# Vue 开发服务器在 5173 端口，Flask 在 5000 端口，端口不同浏览器会拦截
CORS(app)


# ================================================================
# 原有路由（保留不动）—— 给原生的 Jinja2 页面用
# Vue 页面上线前，这些路由继续提供完整功能
# ================================================================

# ----------------------------------------------------------------
# Home — Syllabus page with clickable table of contents
# ----------------------------------------------------------------
@app.route("/")
def syllabus():
    grouped = get_all_topics_grouped()
    flat = get_all_topics()

    if grouped is None or flat is None:
        return render_template("index.html", grouped=None, topics=None)

    return render_template("index.html", grouped=grouped, topics=flat)


# ----------------------------------------------------------------
# Topic detail — show all questions for a given topic
# ----------------------------------------------------------------
@app.route("/topic/<topic_id>")
def topic_detail(topic_id):
    topic = get_topic(topic_id)
    if topic is None:
        abort(404, description=f"Topic '{topic_id}' not found.")

    questions = get_questions_by_topic(topic_id)
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


# ----------------------------------------------------------------
# Serve question images from the output_questions directory
# ----------------------------------------------------------------
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
        topics = search_topics(keyword)
    return render_template("search.html", topics=topics, keyword=keyword)


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html", error_msg=error.description), 404


# ================================================================
# 新增 JSON API 路由 —— 给 Vue 前端调用的接口
#
# 与原路由的区别：
#   原路由 → render_template() → 返回 HTML 页面
#   JSON 路由 → jsonify() → 返回纯 JSON 数据（没有 HTML）
#
# 共同点：都调同一个 database.py，数据源一致
# ================================================================

@app.route("/api/topics")
def api_topics():
    """获取所有 syllabus 主题（扁平列表）"""
    topics = get_all_topics()
    if topics is None:
        return jsonify({"code": 1, "message": "数据库连接失败", "data": None})
    return jsonify({"code": 0, "data": topics})


@app.route("/api/topics/grouped")
def api_topics_grouped():
    """获取按前缀分组后的 syllabus"""
    grouped = get_all_topics_grouped()
    if grouped is None:
        return jsonify({"code": 1, "message": "数据库连接失败", "data": None})
    return jsonify({"code": 0, "data": grouped})


@app.route("/api/topics/<topic_id>")
def api_topic_detail(topic_id):
    """获取某个 topic 的详细信息 + 所有题目"""
    topic = get_topic(topic_id)
    if topic is None:
        return jsonify({
            "code": 1,
            "message": f"Topic '{topic_id}' not found",
            "data": None
        }), 404

    questions = get_questions_by_topic(topic_id) or []

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


@app.route("/api/search")
def api_search():
    """按关键词搜索章节"""
    keyword = request.args.get("q", "").strip()
    if not keyword:
        return jsonify({"code": 0, "data": []})

    topics = search_topics(keyword)
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
