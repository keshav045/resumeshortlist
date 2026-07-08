"""
ranking_engine.py
-----------------
The core ML module — compares resumes to a job description and ranks them.

ML Pipeline:
  1. Preprocess text (lowercase, remove stopwords, stem)
  2. Vectorize using TF-IDF (Term Frequency–Inverse Document Frequency)
  3. Compute Cosine Similarity between each resume and the JD
  4. Sort resumes by score → ranking

Why TF-IDF + Cosine Similarity?
  - TF-IDF gives higher weight to rare, important words (skills, titles)
    and lower weight to common words (the, is, and)
  - Cosine Similarity measures the angle between two document vectors —
    a score of 1.0 = identical, 0.0 = completely unrelated
  - Together they form a simple but surprisingly powerful text matcher
"""

import re
import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

nltk.download('stopwords', quiet=True)
nltk.download('punkt',     quiet=True)

# Stemmer reduces words to their root form
# e.g. "running" → "run", "manages" → "manag"
stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))


def preprocess(text: str) -> str:
    """
    Full NLP preprocessing pipeline:
    1. Lowercase
    2. Remove punctuation / non-alphabetic chars
    3. Tokenize into words
    4. Remove stopwords
    5. Apply Porter Stemming

    Args:
        text: raw resume or JD text

    Returns:
        Single string of cleaned, stemmed tokens
    """
    # Step 1: lowercase
    text = text.lower()

    # Step 2: keep only letters and spaces
    text = re.sub(r'[^a-z\s]', ' ', text)

    # Step 3: split into tokens
    tokens = text.split()

    # Step 4 & 5: filter stopwords and stem
    tokens = [
        stemmer.stem(word)
        for word in tokens
        if word not in stop_words and len(word) > 1
    ]

    return " ".join(tokens)


from backend.skill_extractor import compare_skills


def calculate_match_score(resume_text: str, jd_text: str) -> float:
    """
    Calculates how well a single resume matches the job description using a hybrid score:
    - 50% weight on TF-IDF cosine text similarity
    - 50% weight on Skill Coverage (matching skills / total required skills in JD)

    Args:
        resume_text: raw resume text
        jd_text:     raw job description text

    Returns:
        Float between 0.0 and 100.0 (rounded to 2 decimal places)
    """
    cleaned_resume = preprocess(resume_text)
    cleaned_jd     = preprocess(jd_text)

    # 1. Text Similarity (TF-IDF Cosine Similarity)
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([cleaned_resume, cleaned_jd])
    text_similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0] * 100

    # 2. Skill Coverage
    skill_result = compare_skills(resume_text, jd_text)
    matching = skill_result["matching_skills"]
    missing = skill_result["missing_skills"]

    total_required = len(matching) + len(missing)
    if total_required > 0:
        skill_coverage = (len(matching) / total_required) * 100
        # Hybrid score calculation
        score = (0.50 * text_similarity) + (0.50 * skill_coverage)
    else:
        # Fallback to pure text similarity if JD contains no recognizable skills
        score = text_similarity

    return round(float(score), 2)


def rank_resumes(resumes: list[dict], jd_text: str) -> list[dict]:
    """
    Scores and ranks multiple resumes against one job description.
    Uses the same hybrid score (50% TF-IDF cosine similarity + 50% skill coverage).

    Args:
        resumes: list of dicts, each with at least {"id": ..., "raw_text": ...}
        jd_text: job description text

    Returns:
        Same list sorted by match_score descending, with:
            - "match_score"  added/updated
            - "rank"         added (1 = best match)
    """
    if not resumes:
        return []

    cleaned_jd = preprocess(jd_text)

    # Build a corpus: JD first, then all resumes
    corpus = [cleaned_jd] + [preprocess(r["raw_text"]) for r in resumes]

    vectorizer  = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)

    jd_vector     = tfidf_matrix[0]        # JD row
    resume_matrix = tfidf_matrix[1:]       # all resume rows

    # Compute similarity of every resume vs. the JD
    similarities = cosine_similarity(resume_matrix, jd_vector).flatten()

    # Attach scores to resume dicts using hybrid formula
    for i, resume in enumerate(resumes):
        text_similarity = float(similarities[i]) * 100

        # Calculate skill coverage
        skill_result = compare_skills(resume["raw_text"], jd_text)
        matching = skill_result["matching_skills"]
        missing = skill_result["missing_skills"]

        total_required = len(matching) + len(missing)
        if total_required > 0:
            skill_coverage = (len(matching) / total_required) * 100
            hybrid_score = (0.50 * text_similarity) + (0.50 * skill_coverage)
        else:
            hybrid_score = text_similarity

        resume["match_score"] = round(hybrid_score, 2)

    # Sort by score descending and assign rank
    resumes.sort(key=lambda x: x["match_score"], reverse=True)
    for rank, resume in enumerate(resumes, start=1):
        resume["rank"] = rank

    return resumes


def generate_summary(text: str, max_sentences: int = 3) -> str:
    """
    Creates a short extractive summary of the resume.

    Method: Score each sentence by how many non-stopword tokens it contains
    (a proxy for information density), then return the top N sentences
    in their original order.

    This is a very simple extractive summarizer — no neural networks needed.

    Args:
        text:          full resume text
        max_sentences: how many sentences to include in the summary

    Returns:
        Summary string formatted as a bulleted list
    """
    # Split into sentences (rough split on period/exclamation/question or newline)
    # Since raw text now contains newlines, we can split on both newlines and sentence boundaries
    raw_sentences = re.split(r'(?<=[.!?])\s+|\n', text)
    sentences = []
    for s in raw_sentences:
        s_clean = s.strip()
        # Clean leading bullet symbols if any exist in raw text
        s_clean = re.sub(r'^[•\-\*]\s*', '', s_clean).strip()
        if len(s_clean) > 20:
            sentences.append(s_clean)

    if not sentences:
        fallback_text = text[:300].strip()
        if fallback_text:
            return f"• {fallback_text}..."
        return ""

    # Score each sentence: count meaningful (non-stopword) words
    def sentence_score(sentence: str) -> int:
        words = sentence.lower().split()
        return sum(1 for w in words if w not in stop_words)

    scored = [(s, sentence_score(s)) for s in sentences]

    # Pick top N by score
    top = sorted(scored, key=lambda x: x[1], reverse=True)[:max_sentences]

    # Return them in original order (preserves coherence)
    top_sentences = [s for s, _ in top]
    ordered = [s for s in sentences if s in top_sentences]

    # Format as bulleted list separated by newlines
    bullet_points = [f"• {s}" for s in ordered]
    return "\n".join(bullet_points)
