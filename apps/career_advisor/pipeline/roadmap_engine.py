# Feature: ai-career-advisor
"""
Roadmap Engine — Task 5.1

Pure function. No DB, no filesystem, no network, no RNG, no clock.
Same input always produces the same output.

Roadmap milestones are sourced ONLY from the ROADMAP_TEMPLATES entry
for the top recommended career path. No cross-path data is mixed.

Public API
----------
generate(career_profile: dict, top_path: dict, skill_gap: dict) -> dict

Raises
------
GenerationError on unexpected failures.
"""

from apps.career_advisor.data.roadmap_templates import ROADMAP_TEMPLATES


def generate(career_profile: dict, top_path: dict, skill_gap: dict) -> dict:
    """
    Generate a learning roadmap for the top recommended career path.

    Milestone selection:
      - Only milestones whose 'skill' appears in the skill gap
        (critical or supplementary) are included.
      - For non-senior profiles (entry/junior/mid):
          foundational milestones appear before advanced milestones,
          within each criticality group.
      - For senior profiles:
          foundational milestones are excluded entirely.

    Milestone ordering (overall):
      1. Critical milestones first, then supplementary.
      2. Within each criticality group:
         - non-senior: foundational first (alphabetically), then advanced (alphabetically)
         - senior:     advanced only (alphabetically)

    Empty skill gap → {"career_path": name, "total_duration_weeks": 0, "milestones": []}

    Parameters
    ----------
    career_profile : dict
        Must contain: 'experience_level' (str).
    top_path : dict
        Must contain: 'name' (str).
    skill_gap : dict
        Output of skill_gap_engine.analyse() for top_path["name"].
        Shape: {"critical": [str], "supplementary": [str]}

    Returns
    -------
    dict:
        {
            "career_path":          str,
            "total_duration_weeks": int,
            "milestones": [
                {
                    "title":          str,
                    "description":    str,
                    "duration_weeks": int,
                    "resources":      list[str],
                }
            ]
        }

    Raises
    ------
    GenerationError on unexpected failure.
    """
    try:
        return _generate(career_profile, top_path, skill_gap)
    except GenerationError:
        raise
    except Exception as exc:
        raise GenerationError(f"Roadmap generation failed: {exc}") from exc


def _generate(career_profile: dict, top_path: dict, skill_gap: dict) -> dict:
    path_name = top_path["name"]
    experience_level = career_profile.get("experience_level", "entry")
    is_senior = experience_level == "senior"

    # Retrieve template for this specific path only
    templates = ROADMAP_TEMPLATES.get(path_name, [])

    critical_skills = {s.lower().strip() for s in skill_gap.get("critical", [])}
    supplementary_skills = {s.lower().strip() for s in skill_gap.get("supplementary", [])}
    all_gap_skills = critical_skills | supplementary_skills

    # Empty gap → zero-milestone roadmap
    if not all_gap_skills:
        return {
            "career_path": path_name,
            "total_duration_weeks": 0,
            "milestones": [],
        }

    # Filter templates to only those addressing a skill in the gap
    critical_milestones = []
    supplementary_milestones = []

    for template in templates:
        skill = template.get("skill", "").lower().strip()
        level = template.get("level", "foundational")  # 'foundational' or 'advanced'

        # Exclude foundational milestones entirely for senior profiles
        if is_senior and level == "foundational":
            continue

        # Only include milestones for skills that are in the gap
        if skill in critical_skills:
            critical_milestones.append((template, level))
        elif skill in supplementary_skills:
            supplementary_milestones.append((template, level))
        # Skills not in the gap are excluded — roadmap is gap-specific

    def _sort_key(item):
        """Sort within a criticality group: foundational before advanced, then alpha by title."""
        template, level = item
        level_order = 0 if level == "foundational" else 1
        return (level_order, template.get("title", ""))

    critical_milestones = sorted(critical_milestones, key=_sort_key)
    supplementary_milestones = sorted(supplementary_milestones, key=_sort_key)

    # For senior: sort each group purely alphabetically (foundational already excluded)
    if is_senior:
        critical_milestones = sorted(critical_milestones, key=lambda x: x[0].get("title", ""))
        supplementary_milestones = sorted(supplementary_milestones, key=lambda x: x[0].get("title", ""))

    # Combine: critical first, then supplementary
    ordered = critical_milestones + supplementary_milestones

    # Build clean milestone output dicts (strip internal fields)
    milestones = []
    for template, _level in ordered:
        milestones.append({
            "title": template["title"],
            "description": template["description"],
            "duration_weeks": template["duration_weeks"],
            "resources": list(template["resources"]),  # copy to avoid mutation
        })

    # Cap at 20 milestones per spec
    milestones = milestones[:20]

    total_duration_weeks = sum(m["duration_weeks"] for m in milestones)

    return {
        "career_path": path_name,
        "total_duration_weeks": total_duration_weeks,
        "milestones": milestones,
    }


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class GenerationError(Exception):
    """Raised when roadmap generation fails unexpectedly."""
    pass
