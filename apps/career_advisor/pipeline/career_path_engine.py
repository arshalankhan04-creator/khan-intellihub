# Feature: ai-career-advisor
"""
Career Path Engine — Task 3.1

Pure function. No DB, no filesystem, no network, no RNG, no clock.
Same input always produces the same output.

Public API
----------
recommend(career_profile: dict) -> list[dict]
    Returns 1–5 Career_Path dicts ordered by match_score descending,
    ties broken alphabetically ascending by name.

Raises
------
CatalogueUnavailableError  when CAREER_PATHS is empty.
RecommendError             on unexpected failures.
"""

import math

from apps.career_advisor.data.career_paths import CAREER_PATHS


# ---------------------------------------------------------------------------
# Match score thresholds
# ---------------------------------------------------------------------------
_STRONG_MATCH_THRESHOLD = 50   # score >= 50
_PARTIAL_MATCH_THRESHOLD = 25  # 25 <= score < 50
# Below 25 → low_match

_MAX_RECOMMENDATIONS = 5
_AFFINITY_BOOST_PER_FIELD = 10
_AFFINITY_BOOST_CAP = 20
_SCORE_CAP = 100


def recommend(career_profile: dict) -> list[dict]:
    """
    Return 1–5 career path recommendations ranked by match score.

    Match score formula:
      floor( (|user_skills ∩ path_required_skills| / max(1, |path_required_skills|)) × 100 )
      A path with zero required skills receives score 0.

    Affinity boost (applied before capping):
      +10 if any path keyword appears (case-insensitive substring) in
           career_profile["interests"] (joined)
      +10 if any path keyword appears in career_profile["career_goals"]
      Combined boost capped at +20; final score capped at 100.

    Classification:
      score >= 50  → 'strong_match'
      25–49        → 'partial_match'
      0–24         → 'low_match'

    Ordering: match_score descending; ties broken alphabetically ascending by name.

    Parameters
    ----------
    career_profile : dict
        Must contain: 'skills' (list[str]), 'interests' (list[str]),
        'career_goals' (str).

    Returns
    -------
    list[dict] — each item has: name, match_score, match_level,
                 description, required_skills.

    Raises
    ------
    CatalogueUnavailableError  if CAREER_PATHS is empty.
    RecommendError             on unexpected failure.
    """
    try:
        return _recommend(career_profile)
    except CatalogueUnavailableError:
        raise
    except Exception as exc:
        raise RecommendError(f"Career path recommendation failed: {exc}") from exc


def _recommend(career_profile: dict) -> list[dict]:
    if not CAREER_PATHS:
        raise CatalogueUnavailableError("Career path catalogue is empty.")

    # Normalise user skills to lowercase set for O(1) lookup
    user_skills = {s.lower().strip() for s in career_profile.get("skills", []) if s.strip()}

    # Prepare affinity text for boost checks (lowercase)
    interests_text = " ".join(career_profile.get("interests", [])).lower()
    goals_text = career_profile.get("career_goals", "").lower()

    scored_paths = []
    for path in CAREER_PATHS:
        required = [s.lower().strip() for s in path.get("required_skills", [])]
        total_required = len(required)

        # Base score
        if total_required == 0:
            raw_score = 0
        else:
            matched_count = sum(1 for skill in required if skill in user_skills)
            raw_score = math.floor((matched_count / total_required) * 100)

        # Affinity boost
        boost = _compute_affinity_boost(path.get("keywords", []), interests_text, goals_text)
        final_score = min(_SCORE_CAP, raw_score + boost)

        match_level = _classify(final_score)

        scored_paths.append({
            "name": path["name"],
            "match_score": final_score,
            "match_level": match_level,
            "description": path.get("description", ""),
            "required_skills": required,
            # Internal sort key — removed before returning
            "_sort_name": path["name"],
        })

    # Sort: match_score descending, then name ascending for ties
    scored_paths = sorted(
        scored_paths,
        key=lambda p: (-p["match_score"], p["_sort_name"])
    )

    # Take top 5
    top_paths = scored_paths[:_MAX_RECOMMENDATIONS]

    # Strip internal key
    for p in top_paths:
        del p["_sort_name"]

    return top_paths


def _compute_affinity_boost(keywords: list, interests_text: str, goals_text: str) -> int:
    """
    Compute affinity boost based on path keywords appearing in interests/goals.

    Returns an integer 0, 10, or 20 (never exceeds _AFFINITY_BOOST_CAP).
    A keyword 'matches' if it appears as a substring (case-insensitive)
    in the concatenated interests or career_goals text.
    """
    if not keywords:
        return 0

    boost = 0
    normalised_keywords = [kw.lower().strip() for kw in keywords if kw.strip()]

    # Check interests
    if interests_text and any(kw in interests_text for kw in normalised_keywords):
        boost += _AFFINITY_BOOST_PER_FIELD

    # Check career_goals
    if goals_text and any(kw in goals_text for kw in normalised_keywords):
        boost += _AFFINITY_BOOST_PER_FIELD

    return min(boost, _AFFINITY_BOOST_CAP)


def _classify(score: int) -> str:
    """Map a numeric score to a match level string."""
    if score >= _STRONG_MATCH_THRESHOLD:
        return "strong_match"
    if score >= _PARTIAL_MATCH_THRESHOLD:
        return "partial_match"
    return "low_match"


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class CatalogueUnavailableError(Exception):
    """Raised when the career path catalogue is empty at recommendation time."""
    pass


class RecommendError(Exception):
    """Raised when career path recommendation fails unexpectedly."""
    pass
