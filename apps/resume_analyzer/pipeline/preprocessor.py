"""
Scikit-Learn Preprocessing Layer for Resume Analyzer.

Provides utilities for:
1. Keyword extraction (TF-IDF based)
2. Cosine similarity calculation between resume and job description
3. Cosine similarity-based domain classification
"""

import re
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Predefined industry domain profiles for classification
_DOMAIN_PROFILES = {
    'Software Engineering / IT': (
        "software developer engineer frontend backend fullstack python javascript java react "
        "django docker git aws cloud databases sql postgresql api microservices developer "
        "programming development web coding computer science tech technology git github devops"
    ),
    'Finance / Accounting': (
        "finance financial analyst accounting accountant investment budget budgeting auditing audit tax "
        "spreadsheet portfolio risk wealth banking economics business commerce ledger credit treasury"
    ),
    'Healthcare / Nursing': (
        "healthcare nurse nursing medical patient care clinical treatment hospital medicine physician "
        "health wellness pharmacy therapy clinic diagnosis surgeon emergency medicine dental"
    ),
    'Marketing / Sales': (
        "marketing sales advertising branding brand social media seo sem content campaign "
        "analytics conversion market research customer acquisition relationship management lead public relations"
    ),
    'Human Resources': (
        "hr human resources recruitment recruiter talent acquisition employee relations payroll "
        "onboarding staffing compliance training hiring personnel benefits management compensation"
    ),
    'Education / Training': (
        "teaching education school student teacher curriculum classroom lesson plan instruction "
        "academic learning pedagogy training school college university course professor mentoring"
    ),
}

def clean_text(text: str) -> str:
    """Lowercase text and remove non-alphabetic/numeric characters."""
    if not text:
        return ""
    text = text.lower()
    # Replace newlines/tabs with spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove punctuation but keep alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()

def preprocess_resume(resume_text: str, job_description: str | None = None) -> dict:
    """
    Preprocess resume text using Scikit-Learn.

    Returns:
        dict: {
            'keywords': list of top extracted keywords,
            'job_similarity': float (0.0 to 100.0) or None,
            'classified_domain': str (domain name),
            'domain_confidence': float (similarity score, 0.0 to 100.0)
        }
    """
    cleaned_resume = clean_text(resume_text)
    if not cleaned_resume:
        return {
            'keywords': [],
            'job_similarity': None,
            'classified_domain': 'Unknown',
            'domain_confidence': 0.0
        }

    # 1. Keyword Extraction via TF-IDF
    # We use a simple 1-gram vectorizer
    keywords = []
    try:
        vectorizer = TfidfVectorizer(max_features=50, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([cleaned_resume])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        # Sort keywords by score descending
        keyword_scores = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
        keywords = [kw for kw, score in keyword_scores[:15]]  # Top 15 keywords
    except Exception as exc:
        logger.warning("TF-IDF keyword extraction failed: %s", exc)

    # 2. Cosine Similarity with Job Description
    job_similarity = None
    if job_description and job_description.strip():
        cleaned_jd = clean_text(job_description)
        if cleaned_jd:
            try:
                sim_vectorizer = TfidfVectorizer(stop_words='english')
                tfidf_sim = sim_vectorizer.fit_transform([cleaned_resume, cleaned_jd])
                # Compute cosine similarity between resume (idx 0) and JD (idx 1)
                sim_matrix = cosine_similarity(tfidf_sim[0:1], tfidf_sim[1:2])
                job_similarity = float(sim_matrix[0][0] * 100)  # Convert to percentage
            except Exception as exc:
                logger.warning("Cosine similarity calculation failed: %s", exc)

    # 3. Domain Classification
    # Compare resume against the domain profiles using cosine similarity
    classified_domain = 'General / Other'
    max_similarity = 0.0
    try:
        domain_names = list(_DOMAIN_PROFILES.keys())
        domain_texts = list(_DOMAIN_PROFILES.values())
        
        # Fit vectorizer on resume and all domain texts
        classification_vectorizer = TfidfVectorizer(stop_words='english')
        all_texts = [cleaned_resume] + domain_texts
        tfidf_class = classification_vectorizer.fit_transform(all_texts)
        
        # Compute similarity between resume (idx 0) and all domains (idx 1 onwards)
        class_similarities = cosine_similarity(tfidf_class[0:1], tfidf_class[1:])
        similarities = class_similarities[0]
        
        best_index = int(similarities.argmax())
        best_score = float(similarities[best_index])
        
        # We enforce a small threshold (e.g., 0.05) to classify as a specific domain
        if best_score > 0.05:
            classified_domain = domain_names[best_index]
            max_similarity = best_score * 100
    except Exception as exc:
        logger.warning("Domain classification failed: %s", exc)

    return {
        'keywords': keywords,
        'job_similarity': round(job_similarity, 2) if job_similarity is not None else None,
        'classified_domain': classified_domain,
        'domain_confidence': round(max_similarity, 2)
    }
