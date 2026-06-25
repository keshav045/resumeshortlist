"""
skill_extractor.py
------------------
Extracts technical and soft skills from resume and job description text.

How it works:
- We maintain a master list of known skills (tech + soft).
- We tokenize the input text and check which known skills appear.
- Returns matched/missing skill lists for comparison.
"""

import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Download required NLTK data files on first run
# These are small files (~few MB) downloaded once to ~/.nltk_data
nltk.download('punkt',      quiet=True)
nltk.download('punkt_tab',  quiet=True)
nltk.download('stopwords',  quiet=True)

# ──────────────────────────────────────────────
# Master skill list — extend this for your domain
# ──────────────────────────────────────────────
KNOWN_SKILLS = {
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby",
    "go", "rust", "swift", "kotlin", "php", "r", "scala", "matlab",

    # Web / frontend
    "html", "css", "react", "angular", "vue", "nextjs", "nodejs",
    "express", "django", "flask", "fastapi", "spring", "bootstrap",
    "tailwind",

    # Data & ML
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
    "pandas", "numpy", "matplotlib", "seaborn", "jupyter",
    "data analysis", "data science", "statistics",

    # Databases
    "sql", "mysql", "postgresql", "mongodb", "redis", "sqlite",
    "elasticsearch", "cassandra", "firebase",

    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "ci/cd", "jenkins", "github actions", "linux", "bash",

    # Tools & practices
    "git", "github", "jira", "agile", "scrum", "rest api", "graphql",
    "microservices", "tdd", "unit testing",

    # Soft skills
    "communication", "leadership", "teamwork", "problem solving",
    "critical thinking", "time management", "collaboration",
    "project management", "presentation",
}


def preprocess_text(text: str) -> str:
    """
    Lowercase and lightly clean text before skill matching.
    We keep spaces so multi-word skills (e.g. 'machine learning') still match.
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s\+\#/]', ' ', text)   # keep + # / for c++, c#, ci/cd
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_skills(text: str) -> set:
    """
    Finds which known skills appear in the given text.

    Strategy:
    - For single-word skills: check if the word exists after tokenization
    - For multi-word skills (e.g. "machine learning"): check as substring

    Args:
        text: raw text (resume or job description)

    Returns:
        Set of skill strings that were found
    """
    cleaned = preprocess_text(text)
    found_skills = set()

    for skill in KNOWN_SKILLS:
        if ' ' in skill:
            # Multi-word skill: direct substring search
            if skill in cleaned:
                found_skills.add(skill)
        else:
            # Single-word skill: use word boundaries to avoid partial matches
            # e.g. "r" shouldn't match inside "ruby"
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, cleaned):
                found_skills.add(skill)

    return found_skills


def compare_skills(resume_text: str, jd_text: str) -> dict:
    """
    Compares skills in a resume against a job description.

    Args:
        resume_text: full text of the resume
        jd_text:     full text of the job description

    Returns:
        dict with keys:
            matching_skills  - skills in BOTH resume and JD
            missing_skills   - skills in JD but NOT in resume
            extra_skills     - skills in resume but NOT in JD (bonus)
            resume_skills    - all skills found in resume
            jd_skills        - all skills found in JD
    """
    resume_skills = extract_skills(resume_text)
    jd_skills     = extract_skills(jd_text)

    matching = resume_skills & jd_skills          # intersection
    missing  = jd_skills - resume_skills          # in JD, not in resume
    extra    = resume_skills - jd_skills          # in resume, not in JD

    return {
        "matching_skills": sorted(matching),
        "missing_skills":  sorted(missing),
        "extra_skills":    sorted(extra),
        "resume_skills":   sorted(resume_skills),
        "jd_skills":       sorted(jd_skills),
    }
