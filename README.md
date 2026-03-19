# PaperSplitter 2.0

A comprehensive system for extracting, processing, and organizing past paper questions based on syllabus chapters.

## Architecture Overview

### 1. Data Pipeline (Backend / Offline)

#### PDF Extractor
- **Location**: `backend/offline/extractors/pdf_extractor.py`
- **Purpose**: Reads syllabus PDFs to map out chapters and processes past paper PDFs to slice out individual questions

#### NLP / Mapping Engine
- **Location**: `backend/offline/nlp/nlp_engine.py`
- **Purpose**: Compares past paper questions against syllabus chapters using text embeddings or LLM to determine chapter mappings

#### Database Loader
- **Location**: `backend/offline/loaders/database_loader.py`
- **Purpose**: Saves syllabus structure, sliced questions, and their relationships into the database

### 2. Web Application (Frontend & Backend)

#### Database
- **Location**: `backend/webapp/database/database.py`
- **Purpose**: Stores pre-processed chapters, questions, and their mappings

#### Web Server
- **Location**: `backend/webapp/server/app.py`
- **Purpose**: Python framework that listens for user requests, queries the database for specific chapters, and retrieves linked questions

#### Frontend Template
- **Location**: `backend/webapp/templates/`
- **Purpose**: HTML/CSS pages that render the syllabus and provide clickable links to past paper slices

## Project Structure

```
PaperSplitter2.0/
├── backend/
│   ├── offline/
│   │   ├── extractors/
│   │   │   └── pdf_extractor.py
│   │   ├── nlp/
│   │   │   └── nlp_engine.py
│   │   ├── loaders/
│   │   │   └── database_loader.py
│   │   └── __init__.py
│   └── webapp/
│       ├── database/
│       │   └── database.py
│       ├── server/
│       │   └── app.py
│       ├── templates/
│       │   └── index.html
│       ├── static/
│       │   ├── css/
│       │   │   └── style.css
│       │   └── js/
│       │       └── main.js
│       └── __init__.py
└── frontend/
    └── __init__.py
```

## Setup Instructions

1. Install dependencies (to be determined)
2. Configure environment variables
3. Run the data pipeline to process PDFs
4. Start the web server

## Usage

### Data Pipeline
```bash
python backend/offline/extractors/pdf_extractor.py
python backend/offline/nlp/nlp_engine.py
python backend/offline/loaders/database_loader.py
```

### Web Application
```bash
python backend/webapp/server/app.py
```

## Technologies

- Python
- PDF processing libraries (to be determined)
- NLP/LLM for text embeddings (to be determined)
- Web framework (to be determined)
- Database (to be determined)

## License

MIT License
