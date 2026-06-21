# Khan IntelliHub

An AI-powered career enhancement platform. The MVP delivers a **Resume Analyzer** — upload your resume, receive an ATS compatibility score, and get structured, actionable feedback on how to improve it.

> **Target audience:** This Resume Analyzer is designed and optimised for **Software Engineering and IT resumes**. The scoring engine uses a technology-focused skills corpus and section schema. See [Current Limitations](#current-limitations) for details on non-IT domains.

---

## Current Features (Milestones 1–6)

- **User Registration & Login** — JWT-based authentication with 60-minute access tokens and 7-day refresh tokens
- **Resume Upload** — PDF validation (magic-byte check, 5 MB limit), stored in Supabase Storage
- **Resume Parsing** — Extracts full text and detects six named sections: Contact, Skills, Education, Experience, Projects, Certifications
- **ATS Scoring** — Deterministic rule-based scoring across four weighted categories: Skills Match (40%), Section Completeness (20%), Experience Quality (20%), Content Quality (20%)
- **Feedback Engine** — Generates overall summary, top strengths/weaknesses, prioritised actions, section suggestions, and missing skills analysis
- **Resume History** — Paginated list of all past uploads scoped to the authenticated user
- **Resume Delete** — Removes the database record and the file from Supabase Storage atomically
- **React Frontend** — Full SPA with protected routes, drag-and-drop upload, score gauge, and feedback display

---

## Current Limitations

### Domain Scope

This analyzer is **optimised for Software Engineering and IT roles**. The following assumptions are baked into the current scoring engine:

- **Skills corpus** — The general-purpose skill reference set consists entirely of software technologies (Python, JavaScript, Docker, AWS, Django, React, SQL, etc.). A Civil, Mechanical, or Healthcare resume that does not mention these technologies will receive a significantly lower Skills Match score (40% of the total) even if it is a well-written, competitive resume in its field.

- **Projects section** — The system treats "Projects" as one of six expected resume sections. IT and software resumes commonly have a dedicated Projects section; most non-IT resumes do not. Absence of this section reduces the Section Completeness score and generates feedback suggesting the user add a projects section with links to code repositories — advice that is irrelevant for non-technical roles.

- **Skills advice** — Suggestions reference "Languages, Frameworks, Tools, Cloud" categories and recommend listing 8+ technical skills. These labels are not meaningful for Civil Engineering, MBA, Healthcare, or other professional domains.

- **Certifications examples** — The certifications enhancement tip references AWS, Google Cloud, and Django certifications specifically.

- **GitHub/GitLab recommendations** — The system may suggest adding a GitHub or GitLab profile link regardless of the user's domain.

### Domains that will score less accurately

| Domain | Expected score impact |
|---|---|
| Civil / Structural Engineering | Skills Match likely near 0 without JD; Projects flagged as missing |
| Mechanical / Electrical Engineering | Same as Civil |
| MBA / Business Management | Partial skills overlap (leadership, teamwork); Projects flagged |
| Healthcare / Nursing | Minimal skills overlap; Projects flagged |
| Legal / Law | Minimal skills overlap; Projects flagged |
| Teaching / Education | Minimal skills overlap; Projects flagged |

### Workaround for non-IT users

Provide a **Job Description** when uploading. When a JD is supplied, the skills scoring uses terms extracted from that JD rather than the IT corpus. This significantly improves accuracy for any domain — the system will compare your resume against what the specific job actually requires.

### Planned improvement

A future update will make the scoring engine domain-agnostic by: replacing the general IT corpus with universal professional competencies, making the Projects section optional, and adapting advice language to match the detected domain.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Django 4.2 + Django REST Framework 3.15 |
| Authentication | djangorestframework-simplejwt 5.3 |
| Database | Supabase PostgreSQL (via psycopg v3) |
| File storage | Supabase Storage (via supabase-py) |
| PDF parsing | pdfminer.six |
| Configuration | python-decouple |
| CORS | django-cors-headers |
| Testing | pytest + pytest-django |
| Language | Python 3.14 |
| Frontend | React 18 + Vite 5 |
| HTTP client | Axios |
| Routing | React Router v6 |

---

## Project Structure

```
khan_intellihub/          ← Django project package
├── settings/
│   ├── base.py           ← shared config (DB, JWT, DRF, CORS, throttling)
│   ├── development.py    ← DEBUG=True, browsable API
│   └── production.py     ← HTTPS headers, strict settings
├── urls.py               ← mounts /api/v1/
├── exceptions.py         ← custom DRF exception handler
├── wsgi.py
└── asgi.py

apps/
├── auth_service/         ← registration, login, token refresh
│   ├── models.py         ← CustomUser (UUID PK, email login)
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests/
│
└── resume_analyzer/      ← upload, parse, score, feedback, history, delete
    ├── models.py         ← ResumeRecord
    ├── serializers.py
    ├── views.py
    ├── urls.py
    ├── storage.py        ← Supabase Storage wrapper
    ├── pipeline/
    │   ├── parser.py     ← PDF text extraction + section detection
    │   ├── scorer.py     ← Rule-based ATS scoring
    │   └── feedback.py   ← Feedback report generation
    └── tests/

frontend/                 ← React + Vite SPA
├── src/
│   ├── api/              ← Axios client + service modules
│   ├── context/          ← AuthContext (JWT state)
│   ├── hooks/            ← useAuth, useResumes
│   ├── components/
│   │   ├── common/       ← Navbar, ProtectedRoute, LoadingSpinner, etc.
│   │   ├── auth/         ← LoginForm, RegisterForm
│   │   └── resume/       ← UploadForm, ScoreGauge, FeedbackSection, etc.
│   └── pages/            ← LandingPage, Dashboard, Upload, Results, History
└── .env.example
```

---

## Setup Instructions

### Prerequisites

- Python 3.12+
- Node.js 18+
- A free [Supabase](https://supabase.com) account

### Backend

**1. Clone the repository**
```bash
git clone https://github.com/arshalankhan04-creator/khan-intellihub.git
cd khan-intellihub
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**
```bash
cp .env.example .env
```

Open `.env` and set:

| Variable | Where to find it |
|---|---|
| `SECRET_KEY` | `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DB_HOST` | Supabase → Settings → Database → Host |
| `DB_PASSWORD` | Supabase → Settings → Database → Password |
| `SUPABASE_URL` | Supabase → Settings → API → Project URL |
| `SUPABASE_SERVICE_KEY` | Supabase → Settings → API → service_role key |

**5. Create the storage bucket**

In the Supabase dashboard → Storage → New bucket → Name: `resumes` → Private.

**6. Run migrations**
```bash
python manage.py migrate
```

**7. Start the backend**
```bash
python manage.py runserver
```
API available at `http://127.0.0.1:8000/api/v1/`

### Frontend

```bash
cd frontend
cp .env.example .env        # VITE_API_BASE_URL=http://127.0.0.1:8000
npm install
npm run dev
```
App available at `http://localhost:5173`

### Run tests
```bash
pytest
```

---

## API Reference

All endpoints are under `/api/v1/`. Protected endpoints require `Authorization: Bearer <access_token>`.

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register/` | No | Create account → returns access + refresh tokens |
| `POST` | `/api/v1/auth/login/` | No | Login → returns access + refresh tokens |
| `POST` | `/api/v1/auth/token/refresh/` | No | Exchange refresh token for new access token |

### Resume

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/resumes/upload/` | Yes | Upload PDF, runs full pipeline (parse → score → feedback) |
| `GET` | `/api/v1/resumes/` | Yes | Paginated resume history |
| `GET` | `/api/v1/resumes/{id}/results/` | Yes | Full analysis results for one resume |
| `DELETE` | `/api/v1/resumes/{id}/` | Yes | Delete resume and associated file |

---

## Environment Variables Reference

```
SECRET_KEY             Django secret key
DEBUG                  True / False
ALLOWED_HOSTS          Comma-separated hostnames
DB_HOST                Supabase PostgreSQL host
DB_PORT                5432
DB_NAME                postgres
DB_USER                postgres
DB_PASSWORD            Database password
SUPABASE_URL           https://your-project.supabase.co
SUPABASE_SERVICE_KEY   Supabase service role key
SUPABASE_BUCKET_NAME   resumes
CORS_ALLOWED_ORIGINS   Comma-separated frontend origins
```

---

## Roadmap

| Milestone | Status | Description |
|---|---|---|
| 1 — Auth Backend | ✅ Complete | Registration, login, JWT, rate limiting |
| 2 — Resume Upload & Storage | ✅ Complete | PDF upload, Supabase Storage, history, delete |
| 3 — Resume Parsing | ✅ Complete | PDF text extraction, section detection |
| 4 — ATS Scoring | ✅ Complete | Rule-based scoring across four weighted categories |
| 5 — Feedback Engine | ✅ Complete | Prioritised actions, section suggestions, missing skills |
| 6 — React Frontend | ✅ Complete | Full SPA with protected routes, score display, feedback UI |
| 7 — Domain-Agnostic Scoring | 🔜 Planned | Extend scoring to non-IT domains |

---

## Future Modules

Khan IntelliHub is architected so each new module is an independent Django app:

- **AI Career Advisor** — chat-based career guidance
- **PDF Chatbot** — RAG over uploaded documents
- **Notes Summarizer** — AI-powered notes condensation
- **Interview Prep Tool** — mock interview questions and feedback
- **Smart Business Intelligence Tool** — data insights and reporting

---

## Test Coverage

```
191 tests — 191 passing

Milestone 1 (Auth):     19 tests
Milestone 2 (Upload):   20 tests
Milestone 3 (Parser):   24 tests
Milestone 4 (Scorer):   50 tests
Milestone 5 (Feedback): 78 tests
```

---

## License

MIT
