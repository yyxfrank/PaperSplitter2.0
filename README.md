# PaperSplitter 2.0

A comprehensive system for extracting, processing, and organizing past paper questions based on syllabus chapters. Upload a past paper PDF, and the system automatically classifies each question under the appropriate syllabus topic, slices them into individual PNG images, and serves them through a browsable web interface.

---

## Architecture Overview

PaperSplitter 2.0 is organized into two layers: an **offline data pipeline** that ingests PDFs and populates the database, and a **Flask-based web application** for browsing.

### 1. Offline Data Pipeline

The pipeline is a single-entry script that chains four stages end-to-end.

| Stage | File | Purpose |
|-------|------|---------|
| Syllabus reader | [syllabus_reader.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/offline/extractors/syllabus_reader.py) / [AI_syllabus_reader.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/offline/extractors/AI_syllabus_reader.py) | Parses the syllabus PDF (or JSON) into structured `{topic_id, title, objectives}` records |
| AI classifier | [AI_question_translator.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/offline/extractors/AI_question_translator.py) | Sends each exam question to a GenAI / LLM endpoint to determine which syllabus topic it belongs to |
| PDF slicer | [Question_extractor.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/offline/extractors/Question_extractor.py) | Renders each question as a cropped PNG file |
| Image trimmer | [Blank_remover.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/offline/extractors/Blank_remover.py) | Trims empty whitespace at the bottom of each PNG |
| Database loader | [build_database.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/offline/loaders/build_database.py) | Writes the syllabus topics, questions, and their relations into MySQL |

The orchestrator for the entire pipeline is [pipeline.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/offline/pipeline.py).

### 2. Web Application

| Layer | File | Purpose |
|-------|------|---------|
| Database access | [database.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/webapp/database/database.py) | Centralized MySQL queries (`get_all_topics`, `get_questions_by_topic`, `search_topics`, ...). Connections are opened per call and closed in `finally`. |
| DB configuration | [db_config.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/webapp/database/db_config.py) | Host / user / password / database / charset / collation parameters for MySQL |
| Flask server | [app.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/webapp/server/app.py) | Exposes `/` (syllabus TOC), `/topic/<id>` (question images), `/search` (keyword search), and `/question_images/<path>` (PNG static serving) |
| Templates | [templates/](file:///d:/Python%20Projects/PaperSplitter2.0/backend/webapp/templates/) | `index.html` (home), `topic.html` (per-topic questions), `search.html`, `base.html`, `404.html` |
| Static assets | [static/](file:///d:/Python%20Projects/PaperSplitter2.0/backend/webapp/static/) | `css/style.css`, `js/main.js` |

---

## Project Structure

```
PaperSplitter2.0/
├── backend/
│   ├── offline/
│   │   ├── pipeline.py                 # one-shot orchestrator
│   │   ├── extractors/
│   │   │   ├── AI_question_translator.py
│   │   │   ├── AI_syllabus_reader.py
│   │   │   ├── Blank_remover.py
│   │   │   ├── Question_extractor.py
│   │   │   └── syllabus_reader.py
│   │   ├── loaders/
│   │   │   ├── build_database.py
│   │   │   ├── delete.py
│   │   │   ├── sql_exchange.py
│   │   │   └── test_build_database.py
│   │   └── nlp/
│   │       └── nlp_engine.py
│   └── webapp/
│       ├── database/
│       │   ├── database.py
│       │   └── db_config.py
│       ├── server/
│       │   └── app.py
│       ├── static/
│       │   ├── css/style.css
│       │   └── js/main.js
│       └── templates/
│           ├── base.html
│           ├── index.html
│           ├── topic.html
│           ├── search.html
│           └── 404.html
├── output_questions/                   # generated cropped PNGs (git-ignored)
├── requirements.txt
├── check_paths.py / debug_*.py         # development helpers
└── README.md
```

---

## Setup Instructions

### 1. Install Python dependencies

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows PowerShell
pip install -r requirements.txt
```

The current dependency set is:

- `pymupdf`, `pdfplumber` — PDF parsing and rendering
- `pillow`, `numpy` — image cropping and whitespace trimming
- `flask` — web server and templating
- `google-genai`, `openai` — LLM providers used for syllabus parsing and question classification
- `mysql-connector-python` — MySQL driver (see next step)

### 2. Configure the MySQL database

Open [db_config.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/webapp/database/db_config.py) and fill in your MySQL credentials:

```python
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "your_user",
    "password": "your_password",
    "database": "papersplitter",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "use_pure": True,
}
```

Expected schema — two tables, `syllabus` and `questions`:

- `syllabus(topic_id, title, objectives)` — one row per syllabus topic
- `questions(id, paper_name, question_number, topic_id, image_path, ...)` — one row per extracted question, with a `topic_id` foreign key into `syllabus` and an `idx_topic_id` index for fast lookups

### 3. Prepare the syllabus and API key

- Place a syllabus JSON (e.g. `structured_syllabus_physics.json`) in the project root, or pass `--syllabus path/to/file.json` to the pipeline.
- The AI classifier stage prompts interactively for a GenAI / OpenAI API key at runtime. Export the key as an environment variable if you prefer non-interactive use.

### 4. Run the data pipeline

```bash
python backend\offline\pipeline.py ExperiData\ENGAA_2018_S1_QuestionPaper.pdf
```

Optional flags:

- `--syllabus structured_syllabus_physics.json`
- `--classified classified_questions_physics.json`
- `--db master_exam_data.db` (legacy SQLite path; ignored by the web app which uses MySQL)

The pipeline runs four steps in order and reports progress per stage. Cropped PNGs land in `output_questions/` relative to the project root.

### 5. Start the web server

```bash
python backend\webapp\server\app.py
```

Then open http://127.0.0.1:5000 in your browser.

Available routes:

- `/` — syllabus table of contents (sidebar grouped by chapter prefix P1, P2, M1, …)
- `/topic/<topic_id>` — topic title + objectives, with all related question images grouped by paper
- `/search?q=<keyword>` — keyword search across topic titles and objectives
- `/question_images/<path>` — static PNG serving from `output_questions/`

---

## Engineering Conventions

A few house rules to keep the project maintainable across modules:

- **Centralized queries.** All SQL lives in [database.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/webapp/database/database.py). Route files only import the helper functions, never open their own connections.
- **Close connections per call.** Every helper wraps `cursor` usage in a `try`/`finally { conn.close() }`, so the server never leaks connections under load.
- **Use parameterized queries.** `WHERE title LIKE %s OR objectives LIKE %s`, never f-string interpolation — prevents accidental SQL injection in the search endpoint.
- **Relative image paths in the database.** `image_path` is stored relative to `output_questions/`; the server resolves it through `send_from_directory(IMAGE_BASE_DIR, ...)` so image lookups survive redeploys and path changes.
- **Recursive directory traversal.** Image-processing scripts (e.g. `Blank_remover`) use `os.walk()` to sweep `output_questions/` recursively.

---

## Troubleshooting

- **"No question images found"** on `/topic/<id>` — the pipeline has not been run yet, or `IMAGE_BASE_DIR` does not point at `output_questions/` from the project root.
- **MySQL connection failures** — verify host/user/password/database in [db_config.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/webapp/database/db_config.py), and confirm the target schema has the `syllabus` and `questions` tables.
- **404 on a topic** — the requested `topic_id` is not present in the `syllabus` table. Re-run the pipeline or inspect with `debug_db.py`.

---

## License

MIT License
