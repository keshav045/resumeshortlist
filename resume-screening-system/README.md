# AI Resume Screening System

An intelligent web application that automatically matches resumes to job descriptions using **NLP + Machine Learning**.

Built with **Python**, **FastAPI**, **Scikit-learn**, **NLTK**, and vanilla **JavaScript**.

---

## What It Does

| Feature | Details |
|---|---|
| PDF Resume Upload | Extracts text from any PDF using pdfplumber |
| Job Description Input | Paste any JD via the dashboard |
| TF-IDF + Cosine Similarity | Core ML algorithm that measures text similarity |
| Skill Extraction | Finds matching/missing/extra skills using NLP |
| Match Score (0–100%) | Clear percentage score per resume |
| Resume Ranking | Ranks all resumes in one batch operation |
| PDF Report Download | Professional analysis report via ReportLab |
| SQLite Storage | All resumes and results persisted to a database |
| Dark/Light Mode | Fully themed dashboard |

---

## ML Concepts Used

### TF-IDF (Term Frequency–Inverse Document Frequency)
Converts text into numerical vectors where:
- **TF** = how often a word appears in a document
- **IDF** = how rare the word is across all documents

Rare, important words (like skill names) get higher weights than common words (like "the").

### Cosine Similarity
Measures the angle between two TF-IDF vectors. Score of `1.0` = identical documents, `0.0` = completely unrelated. We convert this to a 0–100% score.

### Extractive Summarization
Scores each sentence by density of meaningful words and returns the top N sentences — no neural networks required.

---

## Project Structure

```
resume-screening-system/
│
├── backend/
│   ├── __init__.py          # Python package marker
│   ├── main.py              # FastAPI app + all API routes
│   ├── models.py            # SQLAlchemy database models
│   ├── database.py          # DB engine + session setup
│   ├── resume_parser.py     # PDF text extraction (pdfplumber)
│   ├── skill_extractor.py   # NLP skill matching
│   ├── ranking_engine.py    # TF-IDF + cosine similarity + ranking
│   └── report_generator.py  # PDF report creation (ReportLab)
│
├── frontend/
│   ├── index.html           # Main dashboard HTML
│   └── static/
│       ├── css/style.css    # Dark/light theme styles
│       └── js/app.js        # Vanilla JS frontend logic
│
├── dataset/
│   ├── uploads/             # Uploaded PDF files stored here
│   └── reports/             # Generated PDF reports
│
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone or download the project
```bash
git clone https://github.com/yourusername/resume-screening-system.git
cd resume-screening-system
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the server
```bash
uvicorn backend.main:app --reload
```

### 5. Open the dashboard
Visit [http://localhost:8000](http://localhost:8000) in your browser.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload-resume` | Upload a PDF resume |
| `POST` | `/job-description` | Set the active JD |
| `POST` | `/match-resume` | Match one resume to JD |
| `GET` | `/rank-resumes` | Rank all resumes |
| `GET` | `/resumes` | List all stored resumes |
| `GET` | `/report/{id}` | Download PDF report |
| `DELETE` | `/resume/{id}` | Delete a resume |

---

## How to Use

1. **Upload** — Go to "Upload Resume", drag-drop one or more PDF resumes.
2. **Job Description** — Paste the JD and save it.
3. **Match** — Pick a resume from the dropdown and run analysis.
4. **Rank** — Switch to "Rankings" and click "Run Ranking" to rank all resumes.
5. **Report** — Click "Download PDF Report" on the match results page.

---

## Interview Talking Points

**Q: Why TF-IDF instead of BERT or word embeddings?**
> TF-IDF is lightweight, interpretable, and requires zero GPU. For keyword-heavy resume matching it performs very well. In production, you'd layer in sentence transformers for semantic matching.

**Q: How does skill extraction work?**
> We maintain a curated skill dictionary and use regex with word boundaries to find exact and multi-word skill matches. It's a keyword approach — more advanced versions use NER (Named Entity Recognition).

**Q: How would you scale this?**
> Replace SQLite with PostgreSQL, add a job queue (Celery + Redis) for async PDF processing, cache TF-IDF models per JD, and deploy on AWS EC2 or Cloud Run.

---

## Version Roadmap

- **v1 (current):** Upload, TF-IDF matching, skill extraction, ranking, PDF reports
- **v2:** Sentence Transformers for semantic similarity, LLM-powered gap analysis
- **v3:** Auth, multi-user, export to ATS, email notifications

---

## Tech Stack

- **FastAPI** — async Python web framework
- **Scikit-learn** — TF-IDF vectorizer + cosine similarity
- **NLTK** — tokenization, stopwords, Porter Stemmer
- **pdfplumber** — reliable PDF text extraction
- **SQLAlchemy** — ORM for SQLite database
- **ReportLab** — PDF report generation
- **Vanilla JS** — no framework frontend
