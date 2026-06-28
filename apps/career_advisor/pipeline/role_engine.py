# Feature: ai-career-advisor
"""
Role Engine — Task 6.1

Pure function. No DB, no filesystem, no network, no RNG, no clock.
Same input always produces the same output.

Role classification is performed ONLY against roles belonging to the
recommended career paths. No universal role list is consulted.

Public API
----------
recommend(career_profile: dict, career_paths: list[dict], skill_gap: dict) -> list[dict]

Raises
------
RecommendError on unexpected failures.
"""

from apps.career_advisor.data.roles import ROLES

_READY_NOW_THRESHOLD = 0.70       # ≥ 70% of role skills covered by user
_READY_AFTER_THRESHOLD = 0.70     # ≥ 70% covered by union(user + gap skills)
_MAX_ROLES = 10
_MIN_ROLES = 3                    # return all if catalogue has fewer qualifying


def recommend(career_profile: dict, career_paths: list[dict], skill_gap: dict) -> list[dict]:
    """
    Return 3–10 role recommendations for the recommended career paths.

    Classification (case-insensitive exact token matching):
      ready_now          : user_skills satisfy >= 70% of role's required skills
      ready_after_roadmap: union(user_skills, all_gap_skills) satisfies >= 70%
      excluded           : neither threshold reached

    If no 'ready_now' role exists across all recommended paths,
    all returned roles will be 'ready_after_roadmap'.

    Parameters
    ----------
    career_profile : dict
        Must contain: 'skills' (list[str]).
    career_paths : list[dict]
        Output of career_path_engine.recommend(); each item has 'name'.
    skill_gap : dict
        Output of skill_gap_engine.analyse().
        Shape: {path_name: {"critical": [...], "supplementary": [...]}}

    Returns
    -------
    list[dict] — each item has: title, career_path, match_level, required_skills.

    Raises
    ------
    RecommendError on unexpected failure.
    """
    try:
        return _recommend(career_profile, career_paths, skill_gap)
    except RecommendError:
        raise
    except Exception as exc:
        raise RecommendError(f"Role recommendation failed: {exc}") from exc


def _recommend(career_profile: dict, career_paths: list[dict], skill_gap: dict) -> list[dict]:
    user_skills = {s.lower().strip() for s in career_profile.get("skills", []) if s.strip()}

    # Build the full set of gap skills across all recommended paths
    all_gap_skills = set()
    for path_gap in skill_gap.values():
        for skill in path_gap.get("critical", []):
            all_gap_skills.add(skill.lower().strip())
        for skill in path_gap.get("supplementary", []):
            all_gap_skills.add(skill.lower().strip())

    # Union of user skills and gap skills (what the user will have after roadmap)
    augmented_skills = user_skills | all_gap_skills

    # Restrict to roles belonging to the recommended paths only
    recommended_path_names = {p["name"] for p in career_paths}
    candidate_roles = [
        r for r in ROLES
        if r.get("career_path") in recommended_path_names
    ]

    qualified = []
    for role in candidate_roles:
        role_required = [s.lower().strip() for s in role.get("required_skills", []) if s.strip()]
        total = len(role_required)

        if total == 0:
            continue  # Skip roles with no defined requirements

        # ready_now check
        now_covered = sum(1 for s in role_required if s in user_skills)
        if (now_covered / total) >= _READY_NOW_THRESHOLD:
            qualified.append({
                "title": role["title"],
                "career_path": role["career_path"],
                "match_level": "ready_now",
                "required_skills": role_required,
            })
            continue

        # ready_after_roadmap check
        after_covered = sum(1 for s in role_required if s in augmented_skills)
        if (after_covered / total) >= _READY_AFTER_THRESHOLD:
            qualified.append({
                "title": role["title"],
                "career_path": role["career_path"],
                "match_level": "ready_after_roadmap",
                "required_skills": role_required,
            })
        # Roles that don't reach 70% even after roadmap → excluded

    # Sort for determinism: ready_now before ready_after_roadmap, then alphabetically by title
    _MATCH_ORDER = {"ready_now": 0, "ready_after_roadmap": 1}
    qualified = sorted(qualified, key=lambda r: (_MATCH_ORDER[r["match_level"]], r["title"]))

    # Return up to _MAX_ROLES; if fewer than _MIN_ROLES qualifying, return all
    return qualified[:_MAX_ROLES]


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class RecommendError(Exception):
    """Raised when role recommendation fails unexpectedly."""
    pass
