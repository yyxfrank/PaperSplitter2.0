import os
import sys
from flask import Flask, render_template, abort, send_from_directory

# Add parent dirs so we can import the database module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.database import (
    get_all_topics,
    get_all_topics_grouped,
    get_topic,
    get_questions_by_topic,
    IMAGE_BASE_DIR,
)

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
)


# ----------------------------------------------------------------
# Home — Syllabus page with clickable table of contents
# ----------------------------------------------------------------
@app.route("/")
def syllabus():
    """Display the full syllabus with a sidebar table of contents."""
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
    """Show the topic title, objectives, and all related question images."""
    topic = get_topic(topic_id)
    if topic is None:
        abort(404, description=f"Topic '{topic_id}' not found.")

    questions = get_questions_by_topic(topic_id)
    if questions is None:
        questions = []

    # Build a lookup of paper_name -> list of question numbers for display
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
    """Serve cropped question PNGs from the output_questions folder."""
    if not os.path.exists(IMAGE_BASE_DIR):
        abort(404, "No question images found. Run the extraction pipeline first.")
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
