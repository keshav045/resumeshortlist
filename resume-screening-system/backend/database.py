"""
database.py
-----------
Sets up the SQLite database using SQLAlchemy ORM.
All uploaded resumes and their analysis results are stored here.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Resolve the project root (one level up from /backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# SQLite database file is stored in the project root
DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'resume_screening.db'}"

# Create the database engine
# check_same_thread=False is needed for SQLite with FastAPI (multiple threads)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Each request gets its own database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all our database models will inherit from
Base = declarative_base()


def get_db():
    """
    Dependency function for FastAPI routes.
    Yields a database session, then closes it when done.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
