# Feature: ai-career-advisor
# Static role catalogue — domain-agnostic.
# All required_skills values are lowercase strings for case-insensitive matching.
# 3–5 role tiers per career path covering entry through senior levels.

ROLES = [
    # ── Full-Stack Developer ──────────────────────────────────────────────────
    {
        "title": "Junior Full-Stack Developer",
        "career_path": "Full-Stack Developer",
        "required_skills": ["javascript", "html", "css", "git", "python"],
    },
    {
        "title": "Full-Stack Developer",
        "career_path": "Full-Stack Developer",
        "required_skills": ["javascript", "react", "python", "django", "sql", "git", "rest api"],
    },
    {
        "title": "Senior Full-Stack Developer",
        "career_path": "Full-Stack Developer",
        "required_skills": [
            "javascript", "react", "python", "django", "sql",
            "git", "rest api", "testing", "css",
        ],
    },
    {
        "title": "Lead Full-Stack Developer",
        "career_path": "Full-Stack Developer",
        "required_skills": [
            "javascript", "react", "python", "django", "sql",
            "git", "rest api", "testing", "html", "css",
        ],
    },

    # ── Data Analyst ─────────────────────────────────────────────────────────
    {
        "title": "Junior Data Analyst",
        "career_path": "Data Analyst",
        "required_skills": ["sql", "excel", "data cleaning", "critical thinking"],
    },
    {
        "title": "Data Analyst",
        "career_path": "Data Analyst",
        "required_skills": ["sql", "excel", "data visualisation", "statistics", "reporting"],
    },
    {
        "title": "Senior Data Analyst",
        "career_path": "Data Analyst",
        "required_skills": [
            "sql", "excel", "data visualisation", "statistics",
            "python", "reporting", "critical thinking",
        ],
    },
    {
        "title": "Lead Data Analyst",
        "career_path": "Data Analyst",
        "required_skills": [
            "sql", "excel", "data visualisation", "statistics",
            "python", "data cleaning", "reporting", "critical thinking",
        ],
    },

    # ── DevOps Engineer ───────────────────────────────────────────────────────
    {
        "title": "Junior DevOps Engineer",
        "career_path": "DevOps Engineer",
        "required_skills": ["linux", "git", "scripting", "networking"],
    },
    {
        "title": "DevOps Engineer",
        "career_path": "DevOps Engineer",
        "required_skills": ["linux", "git", "ci/cd", "containerisation", "cloud platforms", "scripting"],
    },
    {
        "title": "Senior DevOps Engineer",
        "career_path": "DevOps Engineer",
        "required_skills": [
            "linux", "git", "ci/cd", "containerisation",
            "cloud platforms", "scripting", "monitoring", "infrastructure as code",
        ],
    },
    {
        "title": "DevOps Lead",
        "career_path": "DevOps Engineer",
        "required_skills": [
            "linux", "git", "ci/cd", "containerisation", "cloud platforms",
            "scripting", "monitoring", "infrastructure as code", "networking",
        ],
    },

    # ── Civil Engineer ────────────────────────────────────────────────────────
    {
        "title": "Graduate Civil Engineer",
        "career_path": "Civil Engineer",
        "required_skills": ["structural analysis", "autocad", "technical drawing"],
    },
    {
        "title": "Civil Engineer",
        "career_path": "Civil Engineer",
        "required_skills": [
            "structural analysis", "autocad", "project management",
            "surveying", "material science",
        ],
    },
    {
        "title": "Senior Civil Engineer",
        "career_path": "Civil Engineer",
        "required_skills": [
            "structural analysis", "autocad", "project management",
            "surveying", "material science", "hydraulics", "construction management",
        ],
    },
    {
        "title": "Principal Civil Engineer",
        "career_path": "Civil Engineer",
        "required_skills": [
            "structural analysis", "autocad", "project management",
            "material science", "surveying", "hydraulics",
            "construction management", "site supervision", "cost estimation",
        ],
    },

    # ── Mechanical Engineer ───────────────────────────────────────────────────
    {
        "title": "Graduate Mechanical Engineer",
        "career_path": "Mechanical Engineer",
        "required_skills": ["cad design", "technical drawing", "thermodynamics"],
    },
    {
        "title": "Mechanical Engineer",
        "career_path": "Mechanical Engineer",
        "required_skills": [
            "cad design", "thermodynamics", "fluid mechanics",
            "materials engineering", "technical drawing",
        ],
    },
    {
        "title": "Senior Mechanical Engineer",
        "career_path": "Mechanical Engineer",
        "required_skills": [
            "cad design", "thermodynamics", "fluid mechanics",
            "materials engineering", "manufacturing processes",
            "finite element analysis", "technical drawing",
        ],
    },
    {
        "title": "Principal Mechanical Engineer",
        "career_path": "Mechanical Engineer",
        "required_skills": [
            "cad design", "thermodynamics", "fluid mechanics",
            "materials engineering", "manufacturing processes",
            "finite element analysis", "technical drawing", "project management",
        ],
    },

    # ── Financial Analyst ─────────────────────────────────────────────────────
    {
        "title": "Junior Financial Analyst",
        "career_path": "Financial Analyst",
        "required_skills": ["excel", "accounting", "critical thinking", "data analysis"],
    },
    {
        "title": "Financial Analyst",
        "career_path": "Financial Analyst",
        "required_skills": [
            "financial modelling", "excel", "accounting",
            "valuation", "financial reporting",
        ],
    },
    {
        "title": "Senior Financial Analyst",
        "career_path": "Financial Analyst",
        "required_skills": [
            "financial modelling", "excel", "accounting",
            "valuation", "financial reporting", "data analysis", "budgeting",
        ],
    },
    {
        "title": "Finance Manager",
        "career_path": "Financial Analyst",
        "required_skills": [
            "financial modelling", "excel", "accounting", "valuation",
            "financial reporting", "data analysis", "critical thinking",
            "presentation skills", "budgeting",
        ],
    },

    # ── Digital Marketing Specialist ──────────────────────────────────────────
    {
        "title": "Marketing Coordinator",
        "career_path": "Digital Marketing Specialist",
        "required_skills": ["content marketing", "social media management", "copywriting"],
    },
    {
        "title": "Digital Marketing Specialist",
        "career_path": "Digital Marketing Specialist",
        "required_skills": [
            "seo", "content marketing", "social media management",
            "email marketing", "google analytics",
        ],
    },
    {
        "title": "Senior Digital Marketing Specialist",
        "career_path": "Digital Marketing Specialist",
        "required_skills": [
            "seo", "content marketing", "social media management",
            "email marketing", "google analytics", "paid advertising", "a/b testing",
        ],
    },
    {
        "title": "Digital Marketing Manager",
        "career_path": "Digital Marketing Specialist",
        "required_skills": [
            "seo", "content marketing", "social media management",
            "email marketing", "google analytics", "paid advertising",
            "copywriting", "campaign management", "a/b testing",
        ],
    },

    # ── Healthcare Administrator ───────────────────────────────────────────────
    {
        "title": "Healthcare Administrator Trainee",
        "career_path": "Healthcare Administrator",
        "required_skills": ["communication", "record keeping", "patient services"],
    },
    {
        "title": "Healthcare Administrator",
        "career_path": "Healthcare Administrator",
        "required_skills": [
            "healthcare management", "budgeting", "patient services",
            "medical billing", "record keeping",
        ],
    },
    {
        "title": "Senior Healthcare Administrator",
        "career_path": "Healthcare Administrator",
        "required_skills": [
            "healthcare management", "budgeting", "regulatory compliance",
            "patient services", "staff management", "medical billing", "record keeping",
        ],
    },
    {
        "title": "Healthcare Manager",
        "career_path": "Healthcare Administrator",
        "required_skills": [
            "healthcare management", "budgeting", "regulatory compliance",
            "patient services", "staff management", "medical billing",
            "record keeping", "communication", "problem solving",
        ],
    },
]
