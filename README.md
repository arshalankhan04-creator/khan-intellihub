# Khan IntelliHub

An AI-powered career enhancement platform. The MVP delivers a **Resume Analyzer** — upload your resume, receive an ATS compatibility score, and get structured, actionable feedback on how to improve it.

---

## Current Features (Milestones 1–3)

- **User Registration & Login** — JWT-based authentication with 60-minute access tokens and 7-day refresh tokens
- **Resume Upload** — PDF validation (magic-byte check, 5 MB limit), stored in Supabase Storage
- **Resume Parsing** — Extracts full text and detects six named sections: Contact, Skills, Education, Experience, Projects, Certifications
- **Resume History** — Paginated list of all past uploads, scoped to the authenticated user
- **Resume Delete** — Removes the database record and the file from Supabase Storage atomically

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
│   ├── managers.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests/
│
└── resume_analyzer/      ← upload, parse, history, delete
    ├── models.py         ← ResumeRecord
    ├── serializers.py
    ├── views.py
    ├── urls.py
    ├── storage.py        ← Supabase Storage wrapper
    ├── pipeline/
    │   └── parser.py     ← PDF text extraction + section detection
    └── tests/
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/arshalankhan04-creator/khan-intellihub.git
cd khan-intellihub
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Open `.env` and set:

| Variable | Where to find it |
|---|---|
| `SECRET_KEY` | Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DB_HOST` | Supabase → Settings → Database → Host |
| `DB_PASSWORD` | Supabase → Settings → Database → Password |
| `SUPABASE_URL` | Supabase → Settings → API → Project URL |
| `SUPABASE_SERVICE_KEY` | Supabase → Settings → API → service_role key |

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Start the development server

```bash
python manage.py runserver
```

API is available at `http://127.0.0.1:8000/api/v1/`

### 7. Run tests

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
| `POST` | `/api/v1/resumes/upload/` | Yes | Upload PDF, runs parse pipeline |
| `GET` | `/api/v1/resumes/` | Yes | Paginated resume history |
| `GET` | `/api/v1/resumes/{id}/results/` | Yes | Full parsed results for one resume |
| `DELETE` | `/api/v1/resumes/{id}/` | Yes | Delete resume and file |

---

## Environment Variables Reference

See `.env.example` for the full list. Every secret is read from environment variables — nothing is hardcoded.

```
SECRET_KEY          Django secret key
DEBUG               True / False
ALLOWED_HOSTS       Comma-separated hostnames
DB_HOST             Supabase PostgreSQL host
DB_PORT             5432
DB_NAME             postgres
DB_USER             postgres
DB_PASSWORD         Database password
SUPABASE_URL        https://your-project.supabase.co
SUPABASE_SERVICE_KEY  Supabase service role key
SUPABASE_BUCKET_NAME  resumes
CORS_ALLOWED_ORIGINS  Comma-separated frontend origins
```

---

## Roadmap

| Milestone | Status | Description |
|---|---|---|
| 1 — Auth Backend | ✅ Complete | Registration, login, JWT, rate limiting |
| 2 — Resume Upload & Storage | ✅ Complete | PDF upload, Supabase Storage, history, delete |
| 3 — Resume Parsing | ✅ Complete | PDF text extraction, section detection |
| 4 — ATS Scoring | 🔜 Next | Rule-based scoring across keyword, formatting, section, content |
| 5 — Feedback Engine | 🔜 Planned | Categorised, actionable improvement suggestions |
| 6 — React Frontend | 🔜 Planned | React + Vite SPA consuming the REST API |

---

## Future Modules

Khan IntelliHub is architected so each new module is an independent Django app:

- **AI Career Advisor** — chat-based career guidance
- **PDF Chatbot** — RAG over uploaded documents
- **Notes Summarizer** — AI-powered notes condensation
- **Interview Prep Tool** — mock interview questions and feedback

---

## Test Coverage

```
63 tests — 63 passing

Milestone 1 (Auth):    19 tests
Milestone 2 (Upload):  20 tests
Milestone 3 (Parser):  24 tests
```

---

## License

MIT
