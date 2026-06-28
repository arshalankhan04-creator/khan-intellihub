# Feature: ai-career-advisor
"""
Experience Inference Engine — Task 2.1

Pure function. No DB, no filesystem, no network, no RNG, no clock.
Same input always produces the same output.

Public API
----------
infer(experience_text: str) -> str
    Returns one of: 'senior', 'mid', 'junior', 'entry'
"""

import re


# ---------------------------------------------------------------------------
# Signal patterns
# Priority order: senior > mid > junior > entry
# ---------------------------------------------------------------------------

_SENIOR_YEAR_RE = re.compile(r'\b([7-9]|\d{2,})\s*\+?\s*years?\b', re.IGNORECASE)
_SENIOR_TITLE_RE = re.compile(r'\b(senior|lead|principal|director|vp)\b', re.IGNORECASE)

_MID_YEAR_RE = re.compile(r'\b[3-6]\s*years?\b', re.IGNORECASE)
_MID_TITLE_RE = re.compile(r'\b(mid|engineer\s+ii|engineer\s+2|associate)\b', re.IGNORECASE)

_JUNIOR_YEAR_RE = re.compile(r'\b[12]\s*years?\b', re.IGNORECASE)
_JUNIOR_TITLE_RE = re.compile(r'\b(junior|engineer\s+i|engineer\s+1|trainee)\b', re.IGNORECASE)


def infer(experience_text: str) -> str:
    """
    Infer experience level from free-form experience section text.

    Detection strategy (priority: senior > mid > junior > entry):

    Senior signals — whole-word, case-insensitive:
      Year patterns : r'\\b([7-9]|\\d{2,})\\s*\\+?\\s*years?\\b'
      Title patterns: r'\\b(senior|lead|principal|director|vp)\\b'

    Mid signals:
      Year patterns : r'\\b[3-6]\\s*years?\\b'
      Title patterns: r'\\b(mid|engineer\\s+ii|engineer\\s+2|associate)\\b'

    Junior signals:
      Year patterns : r'\\b[12]\\s*years?\\b'
      Title patterns: r'\\b(junior|engineer\\s+i|engineer\\s+1|trainee)\\b'

    Falls back to 'entry' when no signals match.
    Multiple matching levels → highest wins (senior > mid > junior > entry).

    Parameters
    ----------
    experience_text : str
        Raw text from the experience section of a parsed resume.
        May be empty or None.

    Returns
    -------
    str — one of: 'senior', 'mid', 'junior', 'entry'
    """
    if not experience_text or not experience_text.strip():
        return 'entry'

    text = experience_text

    # Senior check first — highest priority
    if _SENIOR_YEAR_RE.search(text) or _SENIOR_TITLE_RE.search(text):
        return 'senior'

    # Mid
    if _MID_YEAR_RE.search(text) or _MID_TITLE_RE.search(text):
        return 'mid'

    # Junior
    if _JUNIOR_YEAR_RE.search(text) or _JUNIOR_TITLE_RE.search(text):
        return 'junior'

    # Default
    return 'entry'


# ---------------------------------------------------------------------------
# Custom exception (kept for structural consistency with other engines)
# ---------------------------------------------------------------------------

class InferenceError(Exception):
    """Raised when experience inference fails unexpectedly."""
    pass
