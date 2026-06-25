"""
main.py
-------
FastAPI backend for the AI Resume Screening System.

Run with:
    uvicorn backend.main:app --reload

API Endpoints:
    POST /upload-resume    → upload a PDF, extract text, store in DB
    POST /job-description  → set the active job description (in memory)
    POST /match-resume     → match a specific resume against the JD
    GET  /rank-resumes     → rank ALL stored resumes against the active JD
    GET  /resumes          → list all stored resumes
    GET  /report/{id}      → download a PDF analysis report
    DELETE /resume/{id}    → delete a resume from the database
"""

import os
import shutil
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.database import engine, get_db, Base
from backend.models import Resume
from backend.resume_parser import extract_text_from_pdf, extract_candidate_name
from backend.skill_extractor import compare_skills
from backend.ranking_engine import calculate_match_score, rank_resumes, generate_summary
from backend.report_generator import generate_pdf_report

# ── App setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Resume Screening System",
    description="Automatically match resumes to job descriptions using NLP",
    version="1.0.0"
)

# Allow frontend (running on a different port) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend HTML/CSS/JS as static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Create DB tables on startup (safe to call repeatedly)
Base.metadata.create_all(bind=engine)

# Temp folder for uploaded PDFs
UPLOAD_DIR = "dataset/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Active job description stored in memory (resets on server restart)
# In production, store this in the database instead
active_job_description: dict = {"text": "", "title": ""}


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Serve the dashboard HTML page."""
    return FileResponse("frontend/index.html")


@app.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF resume.
    - Saves the file to disk
    - Extracts text with pdfplumber
    - Stores in SQLite database
    - Returns the stored resume record
    """
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Save uploaded file to disk
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text from the PDF
    raw_text = extract_text_from_pdf(file_path)
    if not raw_text:
        raise HTTPException(status_code=422, detail="Could not extract text from PDF.")

    # Try to pull the candidate's name from the top of the resume
    candidate_name = extract_candidate_name(raw_text)

    # Generate a short summary using extractive summarization
    summary = generate_summary(raw_text)

    # Save to database
    resume = Resume(
        filename=file.filename,
        candidate_name=candidate_name,
        raw_text=raw_text,
        summary=summary,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {
        "message": "Resume uploaded successfully",
        "id": resume.id,
        "filename": resume.filename,
        "candidate_name": resume.candidate_name,
        "summary": resume.summary,
    }


@app.post("/job-description")
async def set_job_description(
    title: str = Form(""),
    description: str = Form(...)
):
    """
    Set the active job description for matching.
    Stored in memory — all subsequent match/rank calls use this JD.
    """
    if len(description.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Job description is too short. Please provide more detail."
        )

    active_job_description["text"]  = description.strip()
    active_job_description["title"] = title.strip() or "Untitled Position"

    return {
        "message": "Job description saved successfully",
        "title": active_job_description["title"],
        "word_count": len(description.split()),
    }


@app.post("/match-resume")
async def match_resume(
    resume_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Match a specific resume against the active job description.
    Updates the resume record in the database with the new scores.
    """
    if not active_job_description["text"]:
        raise HTTPException(
            status_code=400,
            detail="No job description set. Please POST to /job-description first."
        )

    # Fetch resume from DB
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume ID {resume_id} not found.")

    jd_text = active_job_description["text"]

    # 1. Calculate TF-IDF cosine similarity score
    score = calculate_match_score(resume.raw_text, jd_text)

    # 2. Extract and compare skills
    skill_result = compare_skills(resume.raw_text, jd_text)

    # 3. Update the database record
    resume.match_score     = score
    resume.matching_skills = ", ".join(skill_result["matching_skills"])
    resume.missing_skills  = ", ".join(skill_result["missing_skills"])
    db.commit()
    db.refresh(resume)

    return {
        "id":               resume.id,
        "filename":         resume.filename,
        "candidate_name":   resume.candidate_name,
        "match_score":      resume.match_score,
        "matching_skills":  skill_result["matching_skills"],
        "missing_skills":   skill_result["missing_skills"],
        "extra_skills":     skill_result["extra_skills"],
        "summary":          resume.summary,
        "job_title":        active_job_description["title"],
    }


@app.get("/rank-resumes")
async def rank_all_resumes(db: Session = Depends(get_db)):
    """
    Score and rank ALL resumes in the database against the active JD.
    Uses batch TF-IDF for efficiency.
    """
    if not active_job_description["text"]:
        raise HTTPException(
            status_code=400,
            detail="No job description set. Please POST to /job-description first."
        )

    # Load all resumes from DB
    all_resumes = db.query(Resume).all()
    if not all_resumes:
        return {"message": "No resumes in database.", "rankings": []}

    # Convert SQLAlchemy objects to plain dicts for ranking_engine
    resume_dicts = [
        {"id": r.id, "filename": r.filename, "candidate_name": r.candidate_name,
         "raw_text": r.raw_text, "summary": r.summary}
        for r in all_resumes
    ]

    # Rank them all at once
    ranked = rank_resumes(resume_dicts, active_job_description["text"])

    # Persist the new scores and ranks back to DB
    for item in ranked:
        resume = db.query(Resume).filter(Resume.id == item["id"]).first()
        if resume:
            resume.match_score = item["match_score"]
            resume.rank        = item["rank"]

            skill_result = compare_skills(resume.raw_text, active_job_description["text"])
            resume.matching_skills = ", ".join(skill_result["matching_skills"])
            resume.missing_skills  = ", ".join(skill_result["missing_skills"])

    db.commit()

    # Return top 10
    return {
        "job_title": active_job_description["title"],
        "total_resumes": len(ranked),
        "rankings": [
            {
                "rank":            r["rank"],
                "id":              r["id"],
                "filename":        r["filename"],
                "candidate_name":  r["candidate_name"],
                "match_score":     r["match_score"],
                "summary":         r.get("summary", ""),
            }
            for r in ranked[:10]   # top 10 only
        ]
    }


@app.get("/resumes")
async def list_resumes(db: Session = Depends(get_db)):
    """Return all resumes stored in the database."""
    resumes = db.query(Resume).order_by(Resume.uploaded_at.desc()).all()
    return [
        {
            "id":              r.id,
            "filename":        r.filename,
            "candidate_name":  r.candidate_name,
            "match_score":     r.match_score,
            "rank":            r.rank,
            "uploaded_at":     str(r.uploaded_at),
        }
        for r in resumes
    ]


@app.get("/report/{resume_id}")
async def download_report(resume_id: int, db: Session = Depends(get_db)):
    """
    Generate and download a PDF analysis report for a specific resume.
    Requires the resume to have been matched first.
    """
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    if resume.match_score == 0.0:
        raise HTTPException(
            status_code=400,
            detail="Run /match-resume first to generate analysis data."
        )

    report_path = generate_pdf_report(resume, active_job_description["title"])
    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=f"report_{resume.candidate_name.replace(' ', '_')}.pdf"
    )


@app.delete("/resume/{resume_id}")
async def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    """Delete a resume from the database."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    # Also delete the uploaded file
    file_path = os.path.join(UPLOAD_DIR, resume.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(resume)
    db.commit()
    return {"message": f"Resume '{resume.filename}' deleted successfully."}
