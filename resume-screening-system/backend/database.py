"""
database.py
-----------
Sets up the SQLite database using SQLAlchemy ORM.
All uploaded resumes and their analysis results are stored here.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database file will be created in the project root
DATABASE_URL = "sqlite:///./resume_screening.db"

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
