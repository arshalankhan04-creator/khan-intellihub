"""
ATS Scoring Engine — Milestone 4.

Fully deterministic, rule-based. No ML, no LLMs, no external APIs.
Same input always produces the same output.

Public API
----------
score(parsed_resume: dict, job_description: str | None) -> dict

Output shape
------------
{
    "ats_score":         int,    # 0–100 overall
    "skills_score":      float,  # 0–100  (40% weight)
    "section_score":     float,  # 0–100  (20% weight)
    "experience_score":  float,  # 0–100  (20% weight)
    "content_score":     float,  # 0–100  (20% weight)
    "missing_skills":    [str],  # skills from corpus/JD not found in resume
    "strengths":         [str],  # human-readable positives
    "weaknesses":        [str],  # human-readable areas to improve
}

DB column mapping (ResumeRecord)
---------------------------------
skills_score     → keyword_score
section_score    → section_score
experience_score → formatting_score   (column was pre-created in M2)
content_score    → content_score
"""

import re
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword corpus
# A broad, industry-agnostic set of skills used when no JD is provided.
# Grouped by domain so the list is easy to maintain and extend.
# ---------------------------------------------------------------------------
_GENERAL_SKILLS_CORPUS = {
    # Languages
    'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'go', 'rust',
    'kotlin', 'swift', 'ruby', 'php', 'scala', 'r', 'matlab',
    # Web / frontend
    'html', 'css', 'react', 'vue', 'angular', 'nextjs', 'tailwind', 'bootstrap',
    'sass', 'webpack', 'vite',
    # Backend / frameworks
    'django', 'flask', 'fastapi', 'express', 'spring', 'rails', 'laravel',
    'node', 'nodejs',
    # Databases
    'sql', 'postgresql', 'mysql', 'sqlite', 'mongodb', 'redis', 'supabase',
    'firebase', 'elasticsearch', 'dynamodb',
    # Cloud / DevOps
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'linux',
    'bash', 'git', 'github', 'ci/cd', 'jenkins', 'nginx',
    # Data / ML (general awareness)
    'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'machine learning',
    'deep learning', 'data analysis', 'tableau', 'power bi',
    # APIs / architecture
    'rest', 'graphql', 'grpc', 'microservices', 'api', 'jwt', 'oauth',
    # Soft / process
    'agile', 'scrum', 'jira', 'communication', 'leadership', 'teamwork',
}

# ---------------------------------------------------------------------------
# Action verbs — strong verbs signal impact-driven experience bullets
# ---------------------------------------------------------------------------
_ACTION_VERBS = {
    'achieved', 'architected', 'automated', 'built', 'collaborated', 'created',
    'debugged', 'delivered', 'deployed', 'designed', 'developed', 'drove',
    'engineered', 'enhanced', 'established', 'executed', 'generated', 'implemented',
    'improved', 'increased', 'integrated', 'launched', 'led', 'maintained',
    'managed', 'migrated', 'optimised', 'optimized', 'owned', 'reduced',
    'refactored', 'resolved', 'scaled', 'shipped', 'spearheaded', 'streamlined',
}

# Patterns that indicate quantified impact (numbers / percentages in context)
_QUANTIFICATION_RE = re.compile(
    r'\b(\d+\s*%|\d+x|\d+\+?\s*(users?|customers?|requests?|services?|systems?|'
    r'teams?|engineers?|projects?|products?|clients?|months?|years?|weeks?|days?|'
    r'hours?|minutes?|seconds?|ms|gb|tb|mb|k\b|million|billion))',
    re.IGNORECASE,
)

# Six expected sections — presence and non-emptiness both matter
_EXPECTED_SECTIONS = ['contact', 'skills', 'education', 'experience', 'projects', 'certifications']

# Minimum word counts for "thin" section detection
_SECTION_MIN_WORDS = {
    'contact': 5,
    'skills': 5,
    'education': 10,
    'experience': 20,
    'projects': 10,
    'certifications': 3,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score(parsed_resume: dict, job_description: str | None = None) -> dict:
    """
    Compute a deterministic ATS score from a parsed resume.

    Parameters
    ----------
    parsed_resume  : dict returned by parser.parse()
    job_description: optional plain-text job description

    Returns
    -------
    dict with ats_score, category scores, missing_skills, strengths, weaknesses

    Raises
    ------
    ScoreError on unexpected failure
    """
    try:
        return _compute(parsed_resume, job_description)
    except ScoreError:
        raise
    except Exception as exc:
        logger.exception("Scorer encountered an unexpected error: %s", exc)
        raise ScoreError(f"Scoring failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def _compute(parsed_resume: dict, job_description: str | None) -> dict:
    sections = parsed_resume.get('sections', {})
    raw_text = parsed_resume.get('raw_text', '')
    raw_lower = raw_text.lower()

    # ── 1. Skills Match (40%) ─────────────────────────────────────────────
    skills_score, missing_skills = _score_skills(raw_lower, job_description)

    # ── 2. Section Completeness (20%) ────────────────────────────────────
    section_score, section_weaknesses = _score_sections(sections)

    # ── 3. Experience Quality (20%) ──────────────────────────────────────
    experience_score, experience_notes = _score_experience(sections.get('experience'))

    # ── 4. Resume Content Quality (20%) ──────────────────────────────────
    content_score, content_notes = _score_content(raw_text, sections)

    # ── 5. Weighted overall ───────────────────────────────────────────────
    weighted = (
        skills_score * 0.40
        + section_score * 0.20
        + experience_score * 0.20
        + content_score * 0.20
    )
    ats_score = max(0, min(100, round(weighted)))

    # ── 6. Build strengths / weaknesses lists ────────────────────────────
    strengths, weaknesses = _build_feedback(
        skills_score, section_score, experience_score, content_score,
        missing_skills, section_weaknesses, experience_notes, content_notes,
    )

    return {
        'ats_score': ats_score,
        'skills_score': round(skills_score, 2),
        'section_score': round(section_score, 2),
        'experience_score': round(experience_score, 2),
        'content_score': round(content_score, 2),
        'missing_skills': missing_skills,
        'strengths': strengths,
        'weaknesses': weaknesses,
    }


# ---------------------------------------------------------------------------
# Category scorers
# ---------------------------------------------------------------------------

def _score_skills(raw_lower: str, job_description: str | None) -> tuple[float, list[str]]:
    """
    Skills Match — 40% of overall score.

    Strategy:
    - If a JD is provided: extract unique words from the JD (stop-word filtered,
      len ≥ 3) as the target skill set and compute how many appear in the resume.
    - If no JD: use the _GENERAL_SKILLS_CORPUS as the reference set but only
      count hits from a curated 30-skill "common resume skills" subset so the
      bar is achievable.
    - Score = (matched / total_in_set) * 100, capped at 100.
    - missing_skills = up to 10 target skills absent from the resume.
    """
    if job_description and job_description.strip():
        target_skills = _extract_jd_skills(job_description)
    else:
        # Use a representative 30-skill subset for general scoring
        target_skills = {
            'python', 'javascript', 'sql', 'git', 'rest', 'api', 'linux',
            'html', 'css', 'docker', 'aws', 'django', 'react', 'node',
            'postgresql', 'mongodb', 'java', 'agile', 'ci/cd', 'testing',
            'communication', 'teamwork', 'leadership', 'debugging',
            'data analysis', 'problem solving', 'typescript', 'flask',
            'microservices', 'scrum',
        }

    if not target_skills:
        return 50.0, []  # No reference → neutral score

    matched = {skill for skill in target_skills if skill in raw_lower}
    missing = sorted(target_skills - matched)[:10]  # top 10 missing

    score = (len(matched) / len(target_skills)) * 100
    return min(100.0, score), missing


def _extract_jd_skills(job_description: str) -> set[str]:
    """
    Extract meaningful terms from a job description.

    - Lowercases everything
    - Removes punctuation
    - Filters stop words and single characters
    - Keeps tokens of length ≥ 3
    - Also preserves common multi-word phrases (e.g. 'machine learning')
    Returns a set of skill strings.
    """
    stop_words = {
        'the', 'and', 'for', 'with', 'that', 'this', 'are', 'you', 'will',
        'have', 'from', 'not', 'but', 'can', 'your', 'our', 'their', 'its',
        'all', 'any', 'was', 'were', 'has', 'had', 'been', 'being', 'would',
        'should', 'could', 'may', 'must', 'shall', 'also', 'both', 'each',
        'more', 'most', 'such', 'when', 'who', 'which', 'than', 'then',
        'them', 'they', 'into', 'over', 'after', 'about', 'other', 'some',
        'work', 'role', 'team', 'join', 'like', 'looking', 'candidate',
        'position', 'job', 'opportunity', 'seeking', 'well', 'strong',
        'good', 'great', 'excellent', 'preferred', 'required', 'plus',
    }

    jd_lower = job_description.lower()

    # Check for known multi-word phrases first
    multi_word_phrases = [
        'machine learning', 'deep learning', 'data analysis', 'data science',
        'computer vision', 'natural language processing', 'problem solving',
        'project management', 'software development', 'system design',
        'object oriented', 'test driven', 'ci/cd', 'version control',
    ]
    found_phrases = set()
    for phrase in multi_word_phrases:
        if phrase in jd_lower:
            found_phrases.add(phrase)

    # Single tokens
    tokens = re.findall(r'\b[a-z][a-z0-9+#\-\.]{1,}\b', jd_lower)
    single_skills = {
        t for t in tokens
        if t not in stop_words and len(t) >= 3
    }

    return single_skills | found_phrases


def _score_sections(sections: dict) -> tuple[float, list[str]]:
    """
    Section Completeness — 20% of overall score.

    Each of the 6 expected sections contributes equally (100/6 ≈ 16.67 pts).
    A section earns full points if present AND has enough words.
    It earns half points if present but thin (below _SECTION_MIN_WORDS).
    It earns zero points if absent.
    """
    total_possible = len(_EXPECTED_SECTIONS) * 100.0
    earned = 0.0
    weaknesses = []

    for section_key in _EXPECTED_SECTIONS:
        text = sections.get(section_key)
        if not text or not text.strip():
            weaknesses.append(f"Missing '{section_key}' section")
            continue

        word_count = len(text.split())
        min_words = _SECTION_MIN_WORDS.get(section_key, 5)

        if word_count >= min_words:
            earned += 100.0
        else:
            earned += 50.0  # present but thin
            weaknesses.append(
                f"'{section_key.capitalize()}' section is very short ({word_count} words)"
            )

    score = (earned / total_possible) * 100
    return min(100.0, score), weaknesses


def _score_experience(experience_text: str | None) -> tuple[float, list[str]]:
    """
    Experience Quality — 20% of overall score.

    Evaluates the quality of the experience section using four checks:
    1. Presence (25 pts) — section exists and has content
    2. Action verbs (25 pts) — bullets start with strong action verbs
    3. Quantification (25 pts) — contains numbers/percentages showing impact
    4. Length adequacy (25 pts) — enough words to show substance

    Returns (score 0–100, list of notes for weakness building).
    """
    notes = []

    if not experience_text or not experience_text.strip():
        return 0.0, ['No experience section found']

    score = 0.0
    text_lower = experience_text.lower()
    words = experience_text.split()

    # 1. Presence
    score += 25.0

    # 2. Action verbs
    found_verbs = _ACTION_VERBS & set(re.findall(r'\b\w+\b', text_lower))
    if len(found_verbs) >= 3:
        score += 25.0
    elif len(found_verbs) >= 1:
        score += 12.5
        notes.append('Experience bullets could use more strong action verbs')
    else:
        notes.append('Experience bullets lack action verbs (use: built, led, improved, etc.)')

    # 3. Quantification
    quant_matches = _QUANTIFICATION_RE.findall(experience_text)
    if len(quant_matches) >= 2:
        score += 25.0
    elif len(quant_matches) == 1:
        score += 12.5
        notes.append('Add more quantified achievements (numbers, percentages, scale)')
    else:
        notes.append('No quantified achievements found — add metrics to show impact')

    # 4. Length
    if len(words) >= 80:
        score += 25.0
    elif len(words) >= 30:
        score += 12.5
        notes.append('Experience section is brief — expand with more detail')
    else:
        notes.append('Experience section is very short — add more detail')

    return min(100.0, score), notes


def _score_content(raw_text: str, sections: dict) -> tuple[float, list[str]]:
    """
    Resume Content Quality — 20% of overall score.

    Four checks:
    1. Overall word count (25 pts) — resume has enough content
    2. Contact completeness (25 pts) — email and phone present
    3. Skills diversity (25 pts) — skills section has multiple items
    4. No filler phrases (25 pts) — avoids weak language patterns
    """
    notes = []
    score = 0.0
    words = raw_text.split()

    # 1. Word count
    if len(words) >= 300:
        score += 25.0
    elif len(words) >= 150:
        score += 12.5
        notes.append('Resume is quite short — aim for 300–600 words')
    else:
        notes.append('Resume is too short — add more detail throughout')

    # 2. Contact completeness
    email_re = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
    phone_re = re.compile(r'(\+?\d[\d\s\-().]{7,}\d)')
    has_email = bool(email_re.search(raw_text))
    has_phone = bool(phone_re.search(raw_text))

    if has_email and has_phone:
        score += 25.0
    elif has_email or has_phone:
        score += 12.5
        notes.append('Add both email and phone number to contact information')
    else:
        notes.append('No email or phone number found — add contact details')

    # 3. Skills diversity
    skills_text = sections.get('skills') or ''
    # Count comma-separated or newline-separated skill items
    delimiters = re.compile(r'[,\n|•\-]+')
    skill_items = [s.strip() for s in delimiters.split(skills_text) if s.strip()]
    if len(skill_items) >= 8:
        score += 25.0
    elif len(skill_items) >= 4:
        score += 12.5
        notes.append('Skills section could list more individual skills')
    else:
        notes.append('Skills section is sparse — list at least 8 relevant skills')

    # 4. No filler phrases
    filler_patterns = [
        r'\bteam\s+player\b', r'\bhard[\-\s]?working\b', r'\bpassionate\s+about\b',
        r'\bthink\s+outside\s+the\s+box\b', r'\bgo[\-\s]?getter\b',
        r'\bresults[\-\s]?oriented\b', r'\bself[\-\s]?motivated\b',
        r'\bdetail[\-\s]?oriented\b', r'\bstrong\s+work\s+ethic\b',
        r'\bsynergy\b', r'\bpivot\b', r'\bleverage\b',
    ]
    raw_lower = raw_text.lower()
    filler_found = [p for p in filler_patterns if re.search(p, raw_lower)]

    if not filler_found:
        score += 25.0
    elif len(filler_found) <= 2:
        score += 12.5
        notes.append('Reduce cliché phrases like "team player" or "detail-oriented"')
    else:
        notes.append('Too many cliché filler phrases — replace with specific achievements')

    return min(100.0, score), notes


# ---------------------------------------------------------------------------
# Strengths / weaknesses builder
# ---------------------------------------------------------------------------

def _build_feedback(
    skills_score: float,
    section_score: float,
    experience_score: float,
    content_score: float,
    missing_skills: list,
    section_weaknesses: list,
    experience_notes: list,
    content_notes: list,
) -> tuple[list[str], list[str]]:
    """
    Build human-readable strengths and weaknesses lists from scoring results.
    """
    strengths = []
    weaknesses = []

    # Skills
    if skills_score >= 70:
        strengths.append('Strong skills match for the target role')
    elif skills_score >= 40:
        weaknesses.append(f'Skills match is moderate — consider adding: {", ".join(missing_skills[:5])}')
    else:
        weaknesses.append(f'Low skills match — key missing skills: {", ".join(missing_skills[:5])}')

    # Sections
    if section_score == 100:
        strengths.append('All expected resume sections are present and complete')
    elif section_score >= 67:
        strengths.append('Most resume sections are present')
        weaknesses.extend(section_weaknesses)
    else:
        weaknesses.extend(section_weaknesses)

    # Experience
    if experience_score >= 75:
        strengths.append('Experience section uses strong, impact-focused language')
    elif experience_score >= 50:
        strengths.append('Experience section is present with some good detail')
        weaknesses.extend(experience_notes)
    else:
        weaknesses.extend(experience_notes)

    # Content
    if content_score >= 75:
        strengths.append('Resume has good overall content depth and contact information')
    elif content_score >= 50:
        strengths.append('Resume has reasonable content length')
        weaknesses.extend(content_notes)
    else:
        weaknesses.extend(content_notes)

    # Deduplicate while preserving order
    seen = set()
    unique_strengths = []
    for s in strengths:
        if s not in seen:
            seen.add(s)
            unique_strengths.append(s)

    seen = set()
    unique_weaknesses = []
    for w in weaknesses:
        if w not in seen:
            seen.add(w)
            unique_weaknesses.append(w)

    return unique_strengths, unique_weaknesses


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class ScoreError(Exception):
    """Raised when scoring fails unexpectedly."""
    pass
