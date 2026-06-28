# Feature: ai-career-advisor
"""
Skill Gap Engine — Task 4.1

Pure function. No DB, no filesystem, no network, no RNG, no clock.
Same input always produces the same output.

Skill gap analysis is performed ONLY against each recommended career path's
own required_skills. No universal skill list is used.

Public API
----------
analyse(career_profile: dict, career_paths: list[dict]) -> dict
    Returns a dict keyed by career path name.
    Each value: {"critical": [str], "supplementary": [str]}

Raises
------
AnalysisError on unexpected failures.
"""

from apps.career_advisor.data.roles import ROLES


def analyse(career_profile: dict, career_paths: list[dict]) -> dict:
    """
    Produce a skill gap report for each recommended career path.

    For each path:
      1. Identify skills in path.required_skills absent from user's skills
         (case-insensitive exact token matching).
      2. Classify each missing skill:
         - 'critical'      if required by > 60% of ROLES entries for that path
         - 'supplementary' otherwise
      3. If resume-based mode and career_profile['missing_skills'] is non-empty,
         merge those skills into the report:
         - Skip skills already identified (case-insensitive dedup)
         - Classify merged skills not in path.required_skills as 'supplementary'

    Parameters
    ----------
    career_profile : dict
        Must contain: 'skills' (list[str]), 'missing_skills' (list[str]),
        'mode' (str).
    career_paths : list[dict]
        Output of career_path_engine.recommend(); each item has at least
        'name' and 'required_skills'.

    Returns
    -------
    dict keyed by path name, each value: {"critical": [...], "supplementary": [...]}
    Both arrays are sorted alphabetically for determinism.

    Raises
    ------
    AnalysisError on unexpected failure.
    """
    try:
        return _analyse(career_profile, career_paths)
    except AnalysisError:
        raise
    except Exception as exc:
        raise AnalysisError(f"Skill gap analysis failed: {exc}") from exc


def _analyse(career_profile: dict, career_paths: list[dict]) -> dict:
    # Normalise user skills to a lowercase set
    user_skills = {s.lower().strip() for s in career_profile.get("skills", []) if s.strip()}

    # Resume-based missing_skills (may be empty in manual mode)
    resume_missing = [
        s.lower().strip()
        for s in career_profile.get("missing_skills", [])
        if s.strip()
    ]

    result = {}

    for path in career_paths:
        path_name = path["name"]
        required_skills = [s.lower().strip() for s in path.get("required_skills", [])]

        # Path with zero required skills → empty report
        if not required_skills:
            result[path_name] = {"critical": [], "supplementary": []}
            continue

        # Step 1: compute missing skills from path requirements
        path_missing = [s for s in required_skills if s not in user_skills]

        # Step 2: classify each missing skill by role frequency for this path
        criticality_map = _build_criticality_map(path_name, required_skills)

        critical = []
        supplementary = []

        for skill in path_missing:
            if criticality_map.get(skill, False):
                critical.append(skill)
            else:
                supplementary.append(skill)

        # Step 3: merge resume-sourced missing_skills (resume-based mode only)
        if resume_missing:
            # Track all skills already in the gap (case-insensitive)
            already_in_gap = {s.lower() for s in critical + supplementary}
            # Also exclude skills the user already has
            already_present = user_skills | already_in_gap

            for skill in resume_missing:
                if skill in already_present:
                    continue  # deduplicate
                # Skills not in path's required list → supplementary
                supplementary.append(skill)
                already_present.add(skill)

        # Sort alphabetically for full determinism
        result[path_name] = {
            "critical": sorted(critical),
            "supplementary": sorted(supplementary),
        }

    return result


def _build_criticality_map(path_name: str, required_skills: list) -> dict:
    """
    Build a {skill: is_critical} map for a given career path.

    A skill is 'critical' if it is required by more than 60% of ROLES
    entries for this career path.

    Only skills in required_skills are checked; the result is path-specific.
    No universal skill list is consulted.
    """
    # Filter roles belonging to this path
    path_roles = [r for r in ROLES if r.get("career_path") == path_name]
    total_roles = len(path_roles)

    if total_roles == 0:
        # No roles defined → all missing skills are supplementary
        return {skill: False for skill in required_skills}

    criticality_map = {}
    for skill in required_skills:
        # Count how many roles in this path require this skill
        count = sum(
            1 for role in path_roles
            if skill in {s.lower().strip() for s in role.get("required_skills", [])}
        )
        # Critical if required by MORE than 60% of roles
        criticality_map[skill] = (count / total_roles) > 0.60

    return criticality_map


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class AnalysisError(Exception):
    """Raised when skill gap analysis fails unexpectedly."""
    pass
