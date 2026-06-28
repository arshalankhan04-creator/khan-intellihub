# Feature: ai-career-advisor
# Static next-steps catalogue — domain-agnostic.
# Each entry: priority ('high'|'medium'|'low'), action (≤ 200 chars), category.
# Categories: skill_building, job_search, networking, portfolio, certification.
# Guarantees: ≥ 3 'high', ≥ 3 'medium', ≥ 2 'low'; all five categories covered.

NEXT_STEPS = [
    # ── High priority ─────────────────────────────────────────────────────────
    {
        "priority": "high",
        "action": "Identify 3 job postings that match your target role and list the skills they require.",
        "category": "job_search",
    },
    {
        "priority": "high",
        "action": "Pick the top missing skill from your skill gap report and complete one focused learning resource this week.",
        "category": "skill_building",
    },
    {
        "priority": "high",
        "action": "Update your CV or resume to accurately reflect your current skills, experience, and recent projects.",
        "category": "job_search",
    },
    {
        "priority": "high",
        "action": "Set a specific career goal with a target date and write it down to track your progress.",
        "category": "skill_building",
    },
    {
        "priority": "high",
        "action": "Research the entry-level qualification or certification most valued in your target field and plan how to obtain it.",
        "category": "certification",
    },

    # ── Medium priority ───────────────────────────────────────────────────────
    {
        "priority": "medium",
        "action": "Connect with 2–3 professionals working in your target field on LinkedIn and send a brief, personalised message.",
        "category": "networking",
    },
    {
        "priority": "medium",
        "action": "Complete one small project relevant to your target career path and add it to your portfolio or profile.",
        "category": "portfolio",
    },
    {
        "priority": "medium",
        "action": "Attend a local or virtual industry event, meetup, or webinar related to your career goals.",
        "category": "networking",
    },
    {
        "priority": "medium",
        "action": "Review your LinkedIn profile (or equivalent professional profile) and ensure it matches your updated CV.",
        "category": "job_search",
    },
    {
        "priority": "medium",
        "action": "Find a mentor or career buddy in your target industry and schedule an introductory conversation.",
        "category": "networking",
    },
    {
        "priority": "medium",
        "action": "Enrol in a free online course covering one of your identified skill gaps and complete the first module.",
        "category": "skill_building",
    },

    # ── Low priority ──────────────────────────────────────────────────────────
    {
        "priority": "low",
        "action": "Research industry salary benchmarks for your target role to understand realistic compensation expectations.",
        "category": "job_search",
    },
    {
        "priority": "low",
        "action": "Create or update a personal portfolio page showcasing your work, projects, and key achievements.",
        "category": "portfolio",
    },
    {
        "priority": "low",
        "action": "Read one book or industry report relevant to your target career field to broaden your domain knowledge.",
        "category": "skill_building",
    },
    {
        "priority": "low",
        "action": "Explore professional associations in your field and consider joining one for networking and resources.",
        "category": "networking",
    },
]
