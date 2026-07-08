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
    Removes noise from extracted PDF text while preserving lines/newlines.
    """
    # Remove characters outside standard ASCII range
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # Replace multiple horizontal spaces (but not newlines) with a single space
    text = re.sub(r'[ \t\r\f\v]+', ' ', text)

    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)

    # Strip whitespace from each line and remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    return '\n'.join(lines)


def extract_candidate_name(text: str) -> str:
    """
    Tries to guess the candidate's name from the top of the resume.

    Strategy:
    - Look for capitalized or UPPERCASE words at the top of the resume.
    - Exclude common resume section titles or words (e.g. Resume, CV).
    - If no exact pattern matches, fallback to the first non-empty line
      if it looks reasonable (short, no digits, no emails).
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return "Unknown"

    # Match 2 to 4 words starting with a capital letter or all caps
    name_pattern = re.compile(r'^[A-Z][A-Za-z\.]*(?:\s+[A-Z][A-Za-z\.]*){1,3}$')

    for line in lines[:10]:
        # Clean line from common separators like commas, pipes, or bullets
        clean_line = re.sub(r'[,|•]', ' ', line).strip()
        clean_line = re.sub(r'\s+', ' ', clean_line)

        if name_pattern.match(clean_line):
            lower_line = clean_line.lower()
            ignore_words = {"resume", "cv", "curriculum", "vitae", "summary", "profile", "contact", "email", "phone", "page"}
            if not any(word in lower_line for word in ignore_words) and not any(c.isdigit() for c in clean_line):
                return clean_line

    # Fallback: check if the first line is suitable as a candidate name
    first_line = lines[0]
    clean_first = re.sub(r'[,|•]', ' ', first_line).strip()
    clean_first = re.sub(r'\s+', ' ', clean_first)
    lower_first = clean_first.lower()
    ignore_words = {"resume", "cv", "curriculum", "vitae", "summary", "profile", "contact", "email", "phone", "page"}

    if (len(clean_first.split()) <= 4 and
        not any(c.isdigit() for c in clean_first) and
        "@" not in clean_first and
        ":" not in clean_first and
        not any(word in lower_first for word in ignore_words)):
        return clean_first

    return "Unknown"
