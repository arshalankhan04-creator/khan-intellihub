# Feature: ai-career-advisor
# Static career path catalogue — domain-agnostic.
# All required_skills values are lowercase strings for case-insensitive matching.
# Covers diverse domains: software, engineering, commerce, finance, marketing, healthcare.

CAREER_PATHS = [
    # ── Software / Technology ────────────────────────────────────────────────
    {
        "name": "Full-Stack Developer",
        "description": (
            "Designs and builds end-to-end web applications, owning both the "
            "client-facing interface and the server-side logic and data layer."
        ),
        "required_skills": [
            "javascript", "html", "css", "react", "python", "django",
            "sql", "git", "rest api", "testing",
        ],
        "keywords": [
            "web", "fullstack", "full-stack", "frontend", "backend",
            "developer", "software", "application",
        ],
        "roles": [
            "Junior Full-Stack Developer",
            "Full-Stack Developer",
            "Senior Full-Stack Developer",
            "Lead Full-Stack Developer",
        ],
    },
    {
        "name": "Data Analyst",
        "description": (
            "Collects, processes, and interprets data to support business "
            "decision-making through reports, dashboards, and statistical analysis."
        ),
        "required_skills": [
            "sql", "excel", "data visualisation", "statistics", "python",
            "data cleaning", "reporting", "critical thinking",
        ],
        "keywords": [
            "data", "analytics", "analysis", "business intelligence",
            "reporting", "dashboard", "insights",
        ],
        "roles": [
            "Junior Data Analyst",
            "Data Analyst",
            "Senior Data Analyst",
            "Lead Data Analyst",
        ],
    },
    {
        "name": "DevOps Engineer",
        "description": (
            "Bridges software development and IT operations by automating "
            "build, test, and deployment pipelines and managing cloud infrastructure."
        ),
        "required_skills": [
            "linux", "git", "ci/cd", "containerisation", "cloud platforms",
            "scripting", "networking", "monitoring", "infrastructure as code",
        ],
        "keywords": [
            "devops", "cloud", "infrastructure", "automation",
            "deployment", "operations", "platform",
        ],
        "roles": [
            "Junior DevOps Engineer",
            "DevOps Engineer",
            "Senior DevOps Engineer",
            "DevOps Lead",
        ],
    },
    # ── Engineering (non-software) ────────────────────────────────────────────
    {
        "name": "Civil Engineer",
        "description": (
            "Plans, designs, and oversees construction of infrastructure projects "
            "such as roads, bridges, buildings, and water systems."
        ),
        "required_skills": [
            "structural analysis", "autocad", "project management",
            "material science", "surveying", "hydraulics",
            "construction management", "site supervision", "cost estimation",
        ],
        "keywords": [
            "civil", "construction", "infrastructure", "structural",
            "engineering", "building", "site",
        ],
        "roles": [
            "Graduate Civil Engineer",
            "Civil Engineer",
            "Senior Civil Engineer",
            "Principal Civil Engineer",
        ],
    },
    {
        "name": "Mechanical Engineer",
        "description": (
            "Designs, develops, and tests mechanical systems and devices, "
            "from individual components to large machinery and thermal systems."
        ),
        "required_skills": [
            "cad design", "thermodynamics", "fluid mechanics",
            "materials engineering", "manufacturing processes",
            "finite element analysis", "technical drawing", "project management",
        ],
        "keywords": [
            "mechanical", "manufacturing", "design", "engineering",
            "machinery", "thermal", "production",
        ],
        "roles": [
            "Graduate Mechanical Engineer",
            "Mechanical Engineer",
            "Senior Mechanical Engineer",
            "Principal Mechanical Engineer",
        ],
    },
    # ── Finance / Commerce ────────────────────────────────────────────────────
    {
        "name": "Financial Analyst",
        "description": (
            "Evaluates financial data, prepares forecasts, and advises "
            "organisations on investment decisions and financial planning."
        ),
        "required_skills": [
            "financial modelling", "excel", "accounting", "valuation",
            "financial reporting", "data analysis", "critical thinking",
            "presentation skills", "budgeting",
        ],
        "keywords": [
            "finance", "financial", "investment", "analyst",
            "accounting", "commerce", "banking",
        ],
        "roles": [
            "Junior Financial Analyst",
            "Financial Analyst",
            "Senior Financial Analyst",
            "Finance Manager",
        ],
    },
    # ── Marketing ─────────────────────────────────────────────────────────────
    {
        "name": "Digital Marketing Specialist",
        "description": (
            "Develops and executes online marketing strategies across search, "
            "social, email, and content channels to grow brand awareness and revenue."
        ),
        "required_skills": [
            "seo", "content marketing", "social media management",
            "email marketing", "google analytics", "paid advertising",
            "copywriting", "campaign management", "a/b testing",
        ],
        "keywords": [
            "marketing", "digital", "social media", "seo", "content",
            "advertising", "brand", "campaign",
        ],
        "roles": [
            "Marketing Coordinator",
            "Digital Marketing Specialist",
            "Senior Digital Marketing Specialist",
            "Digital Marketing Manager",
        ],
    },
    # ── Healthcare ────────────────────────────────────────────────────────────
    {
        "name": "Healthcare Administrator",
        "description": (
            "Plans, directs, and coordinates medical and health services "
            "within hospitals, clinics, or other healthcare facilities."
        ),
        "required_skills": [
            "healthcare management", "budgeting", "regulatory compliance",
            "patient services", "staff management", "medical billing",
            "record keeping", "communication", "problem solving",
        ],
        "keywords": [
            "healthcare", "hospital", "medical", "administration",
            "clinical", "health services", "patient",
        ],
        "roles": [
            "Healthcare Administrator Trainee",
            "Healthcare Administrator",
            "Senior Healthcare Administrator",
            "Healthcare Manager",
        ],
    },
]
