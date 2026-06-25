"""
models.py
---------
Database models (tables) for the Resume Screening System.
SQLAlchemy maps these Python classes to SQLite tables automatically.
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from backend.database import Base


class Resume(Base):
    """
    Stores every uploaded resume and its analysis result.

    Table: resumes
    Columns:
        id              - auto-incremented primary key
        filename        - original file name (e.g. "john_doe_resume.pdf")
        candidate_name  - extracted or inferred candidate name
        raw_text        - full extracted text from the PDF
        match_score     - cosine similarity score (0.0 - 100.0)
        matching_skills - comma-separated skills found in both resume & JD
        missing_skills  - comma-separated skills in JD but NOT in resume
        summary         - short auto-generated summary of the resume
        rank            - ranking position vs. other resumes for same JD
        uploaded_at     - timestamp when the resume was uploaded
    """
    __tablename__ = "resumes"

    id              = Column(Integer, primary_key=True, index=True)
    filename        = Column(String(255), nullable=False)
    candidate_name  = Column(String(255), default="Unknown")
    raw_text        = Column(Text, nullable=False)
    match_score     = Column(Float, default=0.0)
    matching_skills = Column(Text, default="")   # stored as comma-separated
    missing_skills  = Column(Text, default="")   # stored as comma-separated
    summary         = Column(Text, default="")
    rank            = Column(Integer, default=0)
    uploaded_at     = Column(DateTime(timezone=True), server_default=func.now())
