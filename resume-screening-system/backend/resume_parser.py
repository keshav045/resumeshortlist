"""
resume_parser.py
----------------
Handles extracting raw text from uploaded PDF resumes.
Uses pdfplumber which is more reliable than PyPDF2 for complex layouts.
"""

import pdfplumber
import re


def extract_text_from_pdf(file_path: str) -> str:
    """
    Reads a PDF file and returns all its text as a single string.

    Args:
        file_path: path to the PDF on disk

    Returns:
        Cleaned string of all text found in the PDF
        Returns empty string if extraction fails
    """
    full_text = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # extract_text() returns None if the page has no text
                page_text = page.extract_text()
                if page_text:
                    full_text.append(page_text)
    except Exception as e:
        print(f"[resume_parser] Error reading PDF: {e}")
        return ""

    # Join all pages with a newline between them
    combined = "\n".join(full_text)
    return clean_text(combined)


def clean_text(text: str) -> str:
    """
    Removes noise from extracted PDF text.

    Steps:
    1. Replace multiple whitespace/newlines with a single space
    2. Remove non-ASCII characters (accented chars, symbols)
    3. Strip leading/trailing whitespace
    """
    # Collapse all whitespace (tabs, newlines, double spaces)
    text = re.sub(r'\s+', ' ', text)

    # Remove characters outside standard ASCII range
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    return text.strip()


def extract_candidate_name(text: str) -> str:
    """
    Tries to guess the candidate's name from the top of the resume.

    Strategy: The first line that looks like "Firstname Lastname"
    (two or more capitalized words, no numbers) is taken as the name.

    This is a heuristic — it won't be perfect for every resume format.

    Args:
        text: full resume text

    Returns:
        Guessed name string, or "Unknown" if none found
    """
    lines = text.strip().split("\n")

    for line in lines[:10]:   # only look at the first 10 lines
        line = line.strip()
        # Match 2-4 words that start with a capital letter, no digits
        if re.match(r'^[A-Z][a-z]+([\s][A-Z][a-z]+){1,3}$', line):
            return line

    return "Unknown"
