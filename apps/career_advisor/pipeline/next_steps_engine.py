# Feature: ai-career-advisor
"""
Next Steps Engine — Task 7.1

Pure function. No DB, no filesystem, no network, no RNG, no clock.
Same input always produces the same output.

Public API
----------
generate(career_profile: dict) -> list[dict]
    Returns 3–7 Actionable_Next_Step dicts ordered high → medium → low.

Raises
------
GenerationError on unexpected failures.
"""

from apps.career_advisor.data.next_steps import NEXT_STEPS

_MIN_STEPS = 3
_MAX_STEPS = 7

# Priority sort order
_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# Injected step when resume-based ats_score < 60
_ATS_IMPROVEMENT_STEP = {
    "priority": "high",
    "action": (
        "Your resume ATS score is below 60. Improve it by adding missing skills, "
        "quantifying experience, and completing all resume sections before applying."
    ),
    "category": "skill_building",
}


def generate(career_profile: dict) -> list[dict]:
    """
    Generate 3–7 prioritised next steps from the static NEXT_STEPS catalogue.

    Rules:
    - Always includes at least one 'high' priority step.
    - If mode is 'resume_based' and ats_score < 60: injects a high-priority
      skill_building step advising resume improvement (deduplicated if
      an equivalent step already exists).
    - Returns items ordered: high → medium → low.

    Parameters
    ----------
    career_profile : dict
        Must contain: 'mode' (str), 'ats_score' (int).

    Returns
    -------
    list[dict] — each item has: priority, action, category.

    Raises
    ------
    GenerationError on unexpected failure.
    """
    try:
        return _generate(career_profile)
    except GenerationError:
        raise
    except Exception as exc:
        raise GenerationError(f"Next steps generation failed: {exc}") from exc


def _generate(career_profile: dict) -> list[dict]:
    mode = career_profile.get("mode", "manual")
    ats_score = career_profile.get("ats_score", 0)

    # Start from a copy of the catalogue to avoid mutating shared state
    steps = [dict(step) for step in NEXT_STEPS]

    # Inject ATS improvement step for resume-based mode with low score
    if mode == "resume_based" and ats_score < 60:
        # Deduplicate: check if an equivalent step already exists
        action_lower = _ATS_IMPROVEMENT_STEP["action"].lower()
        already_present = any(
            s["action"].lower() == action_lower for s in steps
        )
        if not already_present:
            steps = [dict(_ATS_IMPROVEMENT_STEP)] + steps

    # Sort: high → medium → low, then alphabetically by action for full determinism
    steps = sorted(steps, key=lambda s: (_PRIORITY_ORDER.get(s["priority"], 99), s["action"]))

    # Ensure at least one 'high' priority step exists
    # (NEXT_STEPS catalogue guarantees this, but guard defensively)
    has_high = any(s["priority"] == "high" for s in steps)
    if not has_high:
        steps = [dict(_ATS_IMPROVEMENT_STEP)] + steps

    # Clamp to 3–7 items, preserving priority order
    steps = steps[:_MAX_STEPS]

    # If we somehow have fewer than MIN_STEPS, the catalogue is under-populated;
    # return what we have (edge case only)
    return steps


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class GenerationError(Exception):
    """Raised when next steps generation fails unexpectedly."""
    pass
