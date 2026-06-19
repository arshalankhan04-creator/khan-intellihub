"""
Feedback Engine — Milestone 5.

Fully deterministic, rule-based. No ML, no LLMs, no external APIs.
Consumes parsed_resume + scoring_result to produce a structured feedback report.

Public API
----------
generate(parsed_resume: dict, scoring_result: dict, job_description: str | None) -> dict

Output shape (stored in ResumeRecord.feedback_report)
------------------------------------------------------
{
    "overall_summary":   str,
    "top_strengths":     [str],           # up to 5
    "top_weaknesses":    [str],           # up to 5
    "priority_actions":  [
        {"priority": "high"|"medium"|"low", "action": str}
    ],
    "section_suggestions": {
        "contact":        str | null,
        "skills":         str | null,
        "education":      str | null,
        "experience":     str | null,
        "projects":       str | null,
        "certifications": str | null,
    },
    "skills_suggestions":     [str],
    "experience_suggestions": [str],
    "enhancement_tips":       [str],
    "missing_skills":         [str],
}
"""

import re
import logging

logger = logging.getLogger(__name__)

_SECTION_KEYS = ['contact', 'skills', 'education', 'experience', 'projects', 'certifications']

_ACTION_VERBS = {
    'achieved', 'architected', 'automated', 'built', 'collaborated', 'created',
    'debugged', 'delivered', 'deployed', 'designed', 'developed', 'drove',
    'engineered', 'enhanced', 'established', 'executed', 'generated', 'implemented',
    'improved', 'increased', 'integrated', 'launched', 'led', 'maintained',
    'managed', 'migrated', 'optimised', 'optimized', 'owned', 'reduced',
    'refactored', 'resolved', 'scaled', 'shipped', 'spearheaded', 'streamlined',
}

_QUANTIFICATION_RE = re.compile(
    r'\b(\d+\s*%|\d+x|\d+\+?\s*(users?|customers?|requests?|services?|systems?|'
    r'teams?|engineers?|projects?|products?|clients?|months?|years?|weeks?|days?|'
    r'hours?|minutes?|seconds?|ms|gb|tb|mb|k\b|million|billion))',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate(
    parsed_resume: dict,
    scoring_result: dict,
    job_description: str | None = None,
) -> dict:
    """
    Generate a structured feedback report from parsed resume + scoring results.

    Parameters
    ----------
    parsed_resume   : dict returned by parser.parse()
    scoring_result  : dict returned by scorer.score()
    job_description : optional plain-text JD

    Returns
    -------
    dict with all feedback fields

    Raises
    ------
    FeedbackError on unexpected failure
    """
    try:
        return _generate(parsed_resume, scoring_result, job_description)
    except FeedbackError:
        raise
    except Exception as exc:
        logger.exception("Feedback engine encountered an unexpected error: %s", exc)
        raise FeedbackError(f"Feedback generation failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------

def _generate(parsed_resume: dict, scoring_result: dict, job_description: str | None) -> dict:
    sections  = parsed_resume.get('sections', {}) or {}
    raw_text  = parsed_resume.get('raw_text', '') or ''
    ats_score = scoring_result.get('ats_score', 0)
    missing_skills = scoring_result.get('missing_skills', [])
    strengths  = scoring_result.get('strengths', [])
    weaknesses = scoring_result.get('weaknesses', [])

    skills_score     = scoring_result.get('skills_score', 0)
    section_score    = scoring_result.get('section_score', 0)
    experience_score = scoring_result.get('experience_score', 0)
    content_score    = scoring_result.get('content_score', 0)

    overall_summary       = _build_summary(ats_score, skills_score, section_score,
                                           experience_score, content_score)
    top_strengths         = strengths[:5]
    top_weaknesses        = weaknesses[:5]
    section_suggestions   = _build_section_suggestions(sections, section_score)
    skills_suggestions    = _build_skills_suggestions(missing_skills, skills_score,
                                                      sections.get('skills'), job_description)
    experience_suggestions = _build_experience_suggestions(sections.get('experience'),
                                                           experience_score)
    enhancement_tips      = _build_enhancement_tips(raw_text, sections, ats_score)
    priority_actions      = _build_priority_actions(
        ats_score, skills_score, section_score, experience_score, content_score,
        missing_skills, sections,
    )

    return {
        'overall_summary':        overall_summary,
        'top_strengths':          top_strengths,
        'top_weaknesses':         top_weaknesses,
        'priority_actions':       priority_actions,
        'section_suggestions':    section_suggestions,
        'skills_suggestions':     skills_suggestions,
        'experience_suggestions': experience_suggestions,
        'enhancement_tips':       enhancement_tips,
        'missing_skills':         missing_skills,
    }


# ---------------------------------------------------------------------------
# Overall summary
# ---------------------------------------------------------------------------

def _build_summary(ats_score, skills_score, section_score, experience_score, content_score):
    """
    Build a 2-3 sentence human-readable overall summary based on score tiers.
    Fully deterministic: same scores → same summary every time.
    """
    # Tier classification
    if ats_score >= 80:
        tier = 'strong'
    elif ats_score >= 60:
        tier = 'good'
    elif ats_score >= 40:
        tier = 'moderate'
    else:
        tier = 'weak'

    # Opening sentence by tier
    openers = {
        'strong': f"Your resume is well-optimised with an ATS score of {ats_score}/100.",
        'good':   f"Your resume scores {ats_score}/100 and is reasonably competitive.",
        'moderate': f"Your resume scores {ats_score}/100 and has room for improvement.",
        'weak':   f"Your resume scores {ats_score}/100 and needs significant improvement.",
    }

    # Identify the two lowest-scoring categories for the second sentence
    category_scores = {
        'skills match':          skills_score,
        'section completeness':  section_score,
        'experience quality':    experience_score,
        'content quality':       content_score,
    }
    sorted_cats = sorted(category_scores.items(), key=lambda x: x[1])
    lowest_two  = [cat for cat, _ in sorted_cats[:2]]

    middle = (
        f"The areas most impacting your score are {lowest_two[0]} "
        f"and {lowest_two[1]}."
    )

    # Closing sentence by tier
    closers = {
        'strong':   "Focus on the enhancement tips below to push your score even higher.",
        'good':     "Addressing the priority actions below should noticeably improve your score.",
        'moderate': "Follow the priority actions below to make your resume more competitive.",
        'weak':     "Work through the priority actions below to substantially improve your resume.",
    }

    return f"{openers[tier]} {middle} {closers[tier]}"


# ---------------------------------------------------------------------------
# Section suggestions
# ---------------------------------------------------------------------------

_SECTION_ADVICE = {
    'contact': (
        "Ensure your contact section includes full name, professional email, "
        "phone number, city/location, and a LinkedIn URL."
    ),
    'skills': (
        "List 8–15 specific technical skills. Group them by category "
        "(e.g. Languages, Frameworks, Tools) for easier scanning."
    ),
    'education': (
        "Include institution name, degree, field of study, graduation year, "
        "and GPA if above 3.5."
    ),
    'experience': (
        "Use 3–6 bullet points per role starting with strong action verbs. "
        "Each bullet should describe an action, its context, and a measurable result."
    ),
    'projects': (
        "Include 2–4 projects with a title, one-line description, the technologies "
        "used, and a link to the repo or live demo."
    ),
    'certifications': (
        "List certification name, issuing body, and year obtained. "
        "Prioritise certifications relevant to your target role."
    ),
}

_SECTION_THIN_ADVICE = {
    'contact': "Your contact section appears thin — add phone, email, location, and LinkedIn.",
    'skills':  "Your skills section lists very few items — aim for at least 8 distinct skills.",
    'education': (
        "Your education section is brief — include degree title, institution, "
        "graduation year, and GPA."
    ),
    'experience': (
        "Your experience section needs more detail — add 3–5 bullet points per "
        "role with specific achievements."
    ),
    'projects': (
        "Expand your projects section — describe what each project does, "
        "the tech stack used, and link to the code."
    ),
    'certifications': (
        "Your certifications section is very short — list the full certification "
        "name, issuer, and year."
    ),
}

_SECTION_MIN_WORDS = {
    'contact': 5, 'skills': 5, 'education': 10,
    'experience': 20, 'projects': 10, 'certifications': 3,
}


def _build_section_suggestions(sections: dict, section_score: float) -> dict:
    """
    Return a suggestion string (or None) for each of the six sections.
    - Missing section → generic 'add this section' advice
    - Thin section    → specific expansion advice
    - Adequate section → None (no suggestion needed)
    """
    result = {}
    for key in _SECTION_KEYS:
        text = sections.get(key)
        if not text or not text.strip():
            result[key] = f"Add a {key.capitalize()} section. " + _SECTION_ADVICE[key]
        else:
            word_count = len(text.split())
            min_words  = _SECTION_MIN_WORDS.get(key, 5)
            if word_count < min_words:
                result[key] = _SECTION_THIN_ADVICE[key]
            else:
                result[key] = None   # section is adequate
    return result


# ---------------------------------------------------------------------------
# Skills suggestions
# ---------------------------------------------------------------------------

def _build_skills_suggestions(
    missing_skills: list,
    skills_score: float,
    skills_text: str | None,
    job_description: str | None,
) -> list[str]:
    """
    Generate up to 5 actionable skills improvement suggestions.
    """
    suggestions = []

    # 1. Missing skills from JD / corpus
    if missing_skills:
        top_missing = missing_skills[:5]
        suggestions.append(
            f"Add these missing skills to your Skills section: {', '.join(top_missing)}."
        )

    # 2. Skills organisation
    if skills_text:
        skill_count = len([s for s in re.split(r'[,\n|•\-]+', skills_text) if s.strip()])
        if skill_count < 8:
            suggestions.append(
                f"You currently list ~{skill_count} skills. Aim for 8–15 to improve keyword coverage."
            )
        if '\n' not in skills_text and ',' in skills_text:
            suggestions.append(
                "Consider grouping skills by category (Languages, Frameworks, Tools, Cloud) "
                "to improve readability."
            )
    else:
        suggestions.append(
            "Your Skills section is missing entirely. Add a dedicated section listing "
            "your technical skills."
        )

    # 3. JD-specific advice
    if job_description and missing_skills:
        suggestions.append(
            "The job description mentions skills not found in your resume. "
            "Tailor your skills section to match the role's requirements."
        )

    # 4. Skills score-based tip
    if skills_score < 40:
        suggestions.append(
            "Your skills match is low. Review the job description carefully and "
            "add every relevant technology you have experience with."
        )

    return suggestions[:5]


# ---------------------------------------------------------------------------
# Experience suggestions
# ---------------------------------------------------------------------------

def _build_experience_suggestions(
    experience_text: str | None,
    experience_score: float,
) -> list[str]:
    """
    Generate up to 6 actionable experience improvement suggestions.
    """
    suggestions = []

    if not experience_text or not experience_text.strip():
        return [
            "Add an Experience section listing your work history.",
            "For each role include: job title, company, dates, and 3–5 achievement bullets.",
            "If you are a student, include internships, part-time work, or relevant coursework.",
        ]

    text_lower = experience_text.lower()
    words      = experience_text.split()

    # Action verbs check
    found_verbs = _ACTION_VERBS & set(re.findall(r'\b\w+\b', text_lower))
    if len(found_verbs) < 3:
        suggestions.append(
            "Start each experience bullet with a strong action verb such as: "
            "Built, Led, Designed, Improved, Reduced, Automated, Delivered."
        )

    # Quantification check
    quant_matches = _QUANTIFICATION_RE.findall(experience_text)
    if len(quant_matches) < 2:
        suggestions.append(
            "Add measurable outcomes to your bullets — for example: "
            "'Reduced load time by 35%', 'Served 10,000 daily users', "
            "'Led a team of 4 engineers'."
        )

    # Length check
    if len(words) < 50:
        suggestions.append(
            "Your experience section is very short. "
            "Aim for 3–5 detailed bullet points per role."
        )
    elif len(words) < 80:
        suggestions.append(
            "Expand your experience bullets with more context and impact detail."
        )

    # Passive voice detection
    passive_patterns = [r'\bwas\s+\w+ed\b', r'\bwere\s+\w+ed\b', r'\bbeen\s+\w+ed\b']
    has_passive = any(re.search(p, text_lower) for p in passive_patterns)
    if has_passive:
        suggestions.append(
            "Rewrite passive-voice bullets in active voice. "
            "Replace 'Was responsible for building' with 'Built'."
        )

    # Responsibilities vs achievements
    responsibility_phrases = ['responsible for', 'duties included', 'tasked with', 'helped with']
    has_weak_phrases = any(phrase in text_lower for phrase in responsibility_phrases)
    if has_weak_phrases:
        suggestions.append(
            "Replace responsibility-focused language ('responsible for X') with "
            "achievement-focused language ('Delivered X, resulting in Y')."
        )

    return suggestions[:6]


# ---------------------------------------------------------------------------
# Enhancement tips (general resume best practices)
# ---------------------------------------------------------------------------

_FILLER_PATTERNS = [
    (r'\bteam\s+player\b',          'team player'),
    (r'\bhard[\-\s]?working\b',     'hard-working'),
    (r'\bpassionate\s+about\b',     'passionate about'),
    (r'\bresults[\-\s]?oriented\b', 'results-oriented'),
    (r'\bself[\-\s]?motivated\b',   'self-motivated'),
    (r'\bdetail[\-\s]?oriented\b',  'detail-oriented'),
    (r'\bgo[\-\s]?getter\b',        'go-getter'),
    (r'\bstrong\s+work\s+ethic\b',  'strong work ethic'),
    (r'\bsynergy\b',                'synergy'),
    (r'\bthink\s+outside\s+the\s+box\b', 'think outside the box'),
]


def _build_enhancement_tips(raw_text: str, sections: dict, ats_score: int) -> list[str]:
    """
    Generate up to 6 general resume enhancement tips.
    """
    tips = []
    raw_lower = raw_text.lower()
    word_count = len(raw_text.split())

    # 1. Filler phrase removal
    filler_found = [label for pattern, label in _FILLER_PATTERNS
                    if re.search(pattern, raw_lower)]
    if filler_found:
        tips.append(
            f"Remove cliché phrases ({', '.join(filler_found[:3])}) and replace "
            "them with specific, measurable achievements."
        )

    # 2. Length guidance
    if word_count < 150:
        tips.append(
            "Your resume is very short. A strong resume typically contains 300–600 words "
            "of substantive content."
        )
    elif word_count > 900:
        tips.append(
            "Your resume may be too long. Aim to keep it to one or two pages by focusing "
            "on the most relevant and recent experience."
        )

    # 3. Contact information completeness
    email_re = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
    phone_re = re.compile(r'(\+?\d[\d\s\-().]{7,}\d)')
    if not email_re.search(raw_text):
        tips.append("Add a professional email address to your contact information.")
    if not phone_re.search(raw_text):
        tips.append("Add a phone number to your contact information.")

    # 4. LinkedIn / GitHub presence hint
    if 'linkedin' not in raw_lower:
        tips.append(
            "Consider adding your LinkedIn profile URL to make it easy for recruiters "
            "to verify your profile."
        )

    # 5. Projects section advice if absent
    if not sections.get('projects'):
        tips.append(
            "A Projects section significantly strengthens your resume, especially for "
            "developers. Add 2–3 projects you built or contributed to."
        )

    # 6. Certifications value
    if not sections.get('certifications') and ats_score < 70:
        tips.append(
            "Adding industry-recognised certifications (AWS, Google Cloud, Django, etc.) "
            "can improve both your skills score and recruiter confidence."
        )

    return tips[:6]


# ---------------------------------------------------------------------------
# Priority actions
# ---------------------------------------------------------------------------

def _build_priority_actions(
    ats_score: int,
    skills_score: float,
    section_score: float,
    experience_score: float,
    content_score: float,
    missing_skills: list,
    sections: dict,
) -> list[dict]:
    """
    Build a prioritised list of actions:
      high   — directly blocking a competitive score
      medium — meaningful improvement once high-priority items are done
      low    — polish and optimisation

    Returns list of {"priority": str, "action": str}, sorted high → medium → low.
    Each action is a single concrete step.
    """
    actions = []

    # ── HIGH priority ─────────────────────────────────────────────────────

    # Missing critical sections
    for section in ['experience', 'skills', 'contact']:
        if not sections.get(section):
            actions.append({
                'priority': 'high',
                'action': f"Add a {section.capitalize()} section — it is currently missing entirely.",
            })

    # Very low skills match
    if skills_score < 40 and missing_skills:
        top = ', '.join(missing_skills[:4])
        actions.append({
            'priority': 'high',
            'action': f"Add these high-priority missing skills to your resume: {top}.",
        })

    # No experience quantification
    exp_text = sections.get('experience') or ''
    if exp_text and not _QUANTIFICATION_RE.search(exp_text):
        actions.append({
            'priority': 'high',
            'action': (
                "Add at least two quantified achievements to your experience bullets "
                "(e.g. '40% faster', 'served 5,000 users')."
            ),
        })

    # ── MEDIUM priority ───────────────────────────────────────────────────

    # Missing non-critical sections
    for section in ['education', 'projects', 'certifications']:
        if not sections.get(section):
            actions.append({
                'priority': 'medium',
                'action': f"Add a {section.capitalize()} section to make your resume more complete.",
            })

    # Moderate skills gap
    if 40 <= skills_score < 65 and missing_skills:
        top = ', '.join(missing_skills[:3])
        actions.append({
            'priority': 'medium',
            'action': f"Improve your skills match by adding: {top}.",
        })

    # Experience needs action verbs
    if exp_text:
        text_lower = exp_text.lower()
        found_verbs = _ACTION_VERBS & set(re.findall(r'\b\w+\b', text_lower))
        if len(found_verbs) < 3:
            actions.append({
                'priority': 'medium',
                'action': (
                    "Rewrite experience bullets to start with strong action verbs "
                    "(Built, Led, Designed, Improved, Delivered)."
                ),
            })

    # Short resume
    raw_word_count = sum(
        len((sections.get(k) or '').split()) for k in sections
    )
    if raw_word_count < 150:
        actions.append({
            'priority': 'medium',
            'action': "Expand your resume content — it is currently too brief.",
        })

    # ── LOW priority ──────────────────────────────────────────────────────

    # Contact details
    contact_text = (sections.get('contact') or '').lower()
    if 'linkedin' not in contact_text:
        actions.append({
            'priority': 'low',
            'action': "Add your LinkedIn profile URL to your contact section.",
        })

    if 'github' not in contact_text and 'gitlab' not in contact_text:
        actions.append({
            'priority': 'low',
            'action': "Add a GitHub or GitLab profile link to showcase your code.",
        })

    # Skills organisation
    skills_text = sections.get('skills') or ''
    if skills_text and len([s for s in re.split(r'[,\n|•]+', skills_text) if s.strip()]) < 6:
        actions.append({
            'priority': 'low',
            'action': "Expand your Skills section — aim for at least 8 individual skills.",
        })

    # Summary section hint
    if ats_score >= 60:
        actions.append({
            'priority': 'low',
            'action': (
                "Consider adding a two-sentence professional summary at the top "
                "of your resume to immediately convey your value."
            ),
        })

    # Sort: high first, then medium, then low
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    actions.sort(key=lambda x: priority_order[x['priority']])

    # Deduplicate by action text
    seen = set()
    unique = []
    for item in actions:
        if item['action'] not in seen:
            seen.add(item['action'])
            unique.append(item)

    return unique


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class FeedbackError(Exception):
    """Raised when feedback generation fails unexpectedly."""
    pass
