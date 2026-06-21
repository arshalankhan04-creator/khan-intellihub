# Khan IntelliHub — Frontend Design Document
## Milestone 6: Resume Analyzer React + Vite SPA

---

## Overview

The Khan IntelliHub frontend is a React + Vite single-page application. It consumes the versioned REST API exposed by the Django backend (all endpoints under `/api/v1/`). The architecture is deliberately layered so that new modules (AI Career Advisor, PDF Chatbot, Notes Summarizer, Interview Prep, Smart BI Tool) can be added as isolated page + service + component groups without modifying existing code.

---

## Folder Structure

```
frontend/
├── index.html
├── vite.config.js
├── package.json
├── .env                        ← gitignored
├── .env.example                ← committed; documents VITE_API_BASE_URL
│
└── src/
    ├── main.jsx                ← mounts <App /> into #root
    ├── App.jsx                 ← router definition; wraps with AuthProvider
    │
    ├── api/                    ← all HTTP communication lives here
    │   ├── axiosClient.js      ← single Axios instance; JWT inject + refresh interceptors
    │   ├── authService.js      ← register, login, refresh
    │   └── resumeService.js    ← upload, list, results, delete
    │                           ← future: advisorService.js, chatbotService.js, ...
    │
    ├── context/
    │   └── AuthContext.jsx     ← provides { user, accessToken, login, logout, isLoading }
    │
    ├── hooks/
    │   ├── useAuth.js          ← thin wrapper: useContext(AuthContext)
    │   └── useResumes.js       ← data-fetching hook for paginated resume list
    │
    ├── components/
    │   ├── common/             ← module-agnostic shared UI
    │   │   ├── Navbar.jsx
    │   │   ├── ProtectedRoute.jsx
    │   │   ├── PublicRoute.jsx
    │   │   ├── LoadingSpinner.jsx
    │   │   ├── ErrorMessage.jsx
    │   │   └── ConfirmDialog.jsx
    │   │
    │   ├── auth/               ← auth module UI
    │   │   ├── LoginForm.jsx
    │   │   └── RegisterForm.jsx
    │   │
    │   └── resume/             ← resume module UI
    │       ├── UploadForm.jsx
    │       ├── ScoreGauge.jsx
    │       ├── ScoreBreakdown.jsx
    │       ├── FeedbackSection.jsx
    │       ├── PriorityActions.jsx
    │       ├── SectionSuggestions.jsx
    │       ├── MissingSkillsTags.jsx
    │       └── HistoryTable.jsx
    │                           ← future: components/advisor/, components/chatbot/, ...
    │
    ├── pages/
    │   ├── LandingPage.jsx
    │   ├── LoginPage.jsx
    │   ├── RegisterPage.jsx
    │   ├── DashboardPage.jsx
    │   ├── UploadPage.jsx
    │   ├── ResultsPage.jsx
    │   └── HistoryPage.jsx
    │                           ← future: AdvisorPage.jsx, ChatbotPage.jsx, ...
    │
    └── utils/
        ├── formatters.js       ← date formatting, score colour mapping, status label mapping
        └── validators.js       ← email regex, password length check
```

---

## Architecture Decisions

### State Management: React Context (no Redux)

Authentication state is global and needs to be read by the Axios interceptor, Navbar, ProtectedRoute, and every page. A single `AuthContext` covers this cleanly.

Resume list and results are page-level state — fetched on mount, discarded on unmount. No global store needed. `useState` + `useEffect` inside the page component (or a small custom hook) is sufficient.

Redux would be overengineering at this scale. If a future module introduces genuinely complex shared cross-module state, Zustand (lightweight) is the preferred upgrade path — not Redux.

### API Communication: Single Axios Instance

All HTTP calls go through `src/api/axiosClient.js`. This single instance:
- Sets `baseURL` from `import.meta.env.VITE_API_BASE_URL`
- Adds `Content-Type: application/json` by default
- Attaches `Authorization: Bearer <accessToken>` via a request interceptor (reads from AuthContext)
- Handles token refresh via a response interceptor on 401 responses (retries the original request once)
- On refresh failure, clears AuthContext and redirects to `/login`

Each module (auth, resume, future modules) gets its own service file that imports from `axiosClient.js`. No page or component calls Axios directly.

### Routing: React Router v6

```
/                         → LandingPage         (PublicRoute — redirects authed users)
/login                    → LoginPage            (PublicRoute — redirects authed users)
/register                 → RegisterPage         (PublicRoute — redirects authed users)
/dashboard                → DashboardPage        (ProtectedRoute)
/upload                   → UploadPage           (ProtectedRoute)
/results/:resumeId        → ResultsPage          (ProtectedRoute)
/history                  → HistoryPage          (ProtectedRoute)
```

`ProtectedRoute` reads `accessToken` from `AuthContext`. If null, it redirects to `/login?next=<currentPath>`. After login, `LoginPage` reads the `next` param and redirects there.

`PublicRoute` reads `accessToken`. If present, it redirects to `/dashboard`.

---

## Component Design

### `AuthContext` (`src/context/AuthContext.jsx`)

```
State:
  accessToken  string | null   — stored in localStorage
  refreshToken string | null   — stored in localStorage
  userEmail    string | null   — stored in localStorage

Actions:
  login(accessToken, refreshToken, email)
    → stores all three, updates state

  logout()
    → clears localStorage keys, resets state to null

  setAccessToken(token)
    → called by Axios interceptor after a silent refresh

Provided value: { accessToken, userEmail, login, logout, setAccessToken, isAuthenticated }
```

`isAuthenticated` is a derived boolean: `!!accessToken`.

The Axios request interceptor reads `accessToken` from localStorage directly (not through React state) so it works outside the React render cycle.

---

### `axiosClient.js` (`src/api/axiosClient.js`)

```
const client = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL })

Request interceptor:
  reads accessToken from localStorage
  adds Authorization: Bearer <token> if present

Response interceptor:
  on 401:
    reads refreshToken from localStorage
    calls POST /api/v1/auth/token/refresh/ with { refresh: refreshToken }
    on success: stores new accessToken in localStorage + AuthContext, retries original request
    on failure: clears localStorage, navigates to /login
  on all other errors: rejects with the error as-is
```

A `_retry` flag on the original request config prevents infinite retry loops.

---

### `ProtectedRoute` / `PublicRoute`

```jsx
// ProtectedRoute — wraps protected pages
function ProtectedRoute() {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  if (!isAuthenticated) return <Navigate to={`/login?next=${location.pathname}`} replace />
  return <Outlet />
}

// PublicRoute — wraps login/register
function PublicRoute() {
  const { isAuthenticated } = useAuth()
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <Outlet />
}
```

---

### `Navbar` (`src/components/common/Navbar.jsx`)

Renders on all pages inside the authenticated layout. Shows:
- Brand name "Khan IntelliHub" (links to `/dashboard`)
- Navigation links: Dashboard, Upload, History
- User email display
- Logout button (calls `logout()` from `useAuth()`, navigates to `/`)

Does NOT render on the landing, login, or register pages.

---

### `UploadForm` (`src/components/resume/UploadForm.jsx`)

Props: `onSuccess(resumeId)`, `onError(message)`

Internal state:
- `selectedFile` — the File object chosen by the user
- `jobDescription` — textarea value
- `isLoading` — boolean for submission in progress
- `error` — inline error string

The file input accepts `.pdf` only. The drag-and-drop zone uses standard HTML5 drag events (`onDragOver`, `onDrop`). On file drop/selection, displays the filename. On submit, calls `resumeService.uploadResume(file, jobDescription)`. On success, calls `onSuccess(resumeId)`.

---

### `ScoreGauge` (`src/components/resume/ScoreGauge.jsx`)

Props: `score` (integer 0–100)

Displays the ATS score as a large centered number with a circular SVG arc. Colour-codes by tier:
- 0–39 → red
- 40–59 → orange
- 60–79 → yellow
- 80–100 → green

Purely presentational — no data fetching.

---

### `ScoreBreakdown` (`src/components/resume/ScoreBreakdown.jsx`)

Props: `scores` object `{ skills_match, section_completeness, experience_quality, content_quality }`

Renders four labelled horizontal progress bars, each showing the category name, weight, and score value.

---

### `FeedbackSection` (`src/components/resume/FeedbackSection.jsx`)

Props: `feedbackReport` object

Renders all feedback sub-sections:
- Overall Summary paragraph
- Top Strengths as a bulleted list with a green check icon per item
- Top Weaknesses as a bulleted list with a red X icon per item
- `<PriorityActions>` sub-component
- `<SectionSuggestions>` sub-component
- Skills Suggestions list
- Experience Suggestions list
- Enhancement Tips list
- `<MissingSkillsTags>` sub-component

---

### `PriorityActions` (`src/components/resume/PriorityActions.jsx`)

Props: `actions` array of `{ priority, action }`

Groups actions into three collapsible sections: High Priority, Medium Priority, Low Priority. Each action is a card with a coloured left border:
- high → red
- medium → amber
- low → grey

---

### `SectionSuggestions` (`src/components/resume/SectionSuggestions.jsx`)

Props: `suggestions` object `{ contact, skills, education, experience, projects, certifications }`

Renders only sections where the value is non-null. Each non-null section renders as a card with the section name as a heading and the suggestion text as the body. Null sections are silently omitted.

---

### `MissingSkillsTags` (`src/components/resume/MissingSkillsTags.jsx`)

Props: `skills` array of strings

Renders each missing skill as a small rounded pill/tag with a muted colour. If the array is empty, renders nothing.

---

### `HistoryTable` (`src/components/resume/HistoryTable.jsx`)

Props: `records`, `totalCount`, `page`, `pageSize`, `onPageChange`, `onDelete`

Renders a table with columns: Filename, Uploaded, Status, ATS Score, Actions.

Status badge colours (implemented via a `formatters.js` helper):
- `COMPLETED` → green badge
- `PENDING` / `PARSED` / `SCORED` → yellow badge
- `*_FAILED` → red badge

Each row's "View" button navigates to `/results/:resumeId`. Each row's "Delete" button calls `onDelete(resumeId)`.

Pagination: Previous button (disabled on page 1), page indicator ("Page 2 of 5"), Next button (disabled on last page).

---

### `ConfirmDialog` (`src/components/common/ConfirmDialog.jsx`)

Props: `isOpen`, `message`, `onConfirm`, `onCancel`

A simple modal overlay with a message, a Confirm button, and a Cancel button. Used for the delete confirmation flow. Not tied to resume logic — reusable by any future module.

---

## Page Design

### `LandingPage` (`/`)

Sections:
1. Hero — headline, subtitle, two CTA buttons (Register, Login)
2. Features — three feature cards: "Upload Your Resume", "Get Your ATS Score", "Receive Actionable Feedback"
3. Footer — "Khan IntelliHub © 2025"

No API calls. No auth check (accessible to everyone).

---

### `LoginPage` (`/login`)

Renders `LoginForm`. On successful login:
1. Calls `login(access, refresh, email)` from `useAuth()`
2. Reads `?next=` query param
3. Navigates to `next` or `/dashboard`

---

### `RegisterPage` (`/register`)

Renders `RegisterForm`. On successful registration:
1. Calls `login(access, refresh, email)` from `useAuth()` (register returns tokens too)
2. Navigates to `/dashboard`

---

### `DashboardPage` (`/dashboard`)

On mount: calls `resumeService.listResumes({ page: 1, page_size: 50 })` to get total count and last ATS score.

Renders:
- "Welcome back, {email}"
- Total resumes uploaded count
- Highest ATS score achieved (or "—" if none)
- Two quick-action cards: "Analyze a Resume" → `/upload` and "View History" → `/history`
- If total count is 0: empty state card with "Upload your first resume to get started"

---

### `UploadPage` (`/upload`)

Renders `UploadForm`. On `onSuccess(resumeId)`:
- Navigates to `/results/${resumeId}`

On `onError(message)`:
- Displays error inline (handled inside `UploadForm`)

No additional state at the page level.

---

### `ResultsPage` (`/results/:resumeId`)

On mount: calls `resumeService.getResults(resumeId)`.

States:
- `isLoading` → shows `LoadingSpinner`
- `error` → shows `ErrorMessage` (404, 403, or 422 with reason)
- `data` → renders the full results layout:
  - `ScoreGauge` (ats_score)
  - `ScoreBreakdown` (scores object)
  - `FeedbackSection` (feedback_report object)
  - "Back to History" link → `/history`

---

### `HistoryPage` (`/history`)

State: `page` (integer, starts at 1), `records`, `totalCount`, `isLoading`, `deletingId`

On mount and on page change: calls `resumeService.listResumes({ page, page_size: 10 })`.

Delete flow:
1. User clicks Delete → `ConfirmDialog` opens
2. User confirms → calls `resumeService.deleteResume(resumeId)` with `deletingId` set
3. On 204 → removes record from local state, hides dialog, clears `deletingId`
4. On error → shows inline error, clears `deletingId`

Renders `HistoryTable` + `ConfirmDialog`.

---

## API Service Layer

### `authService.js`

```js
register(email, password)       → POST /api/v1/auth/register/
login(email, password)          → POST /api/v1/auth/login/
refreshToken(refresh)           → POST /api/v1/auth/token/refresh/
```

### `resumeService.js`

```js
uploadResume(file, jobDescription) → POST /api/v1/resumes/upload/  (multipart/form-data)
listResumes({ page, page_size })   → GET  /api/v1/resumes/
getResults(resumeId)               → GET  /api/v1/resumes/:resumeId/results/
deleteResume(resumeId)             → DELETE /api/v1/resumes/:resumeId/
```

All functions return the `response.data` payload. Error handling is done in the calling component via try/catch. The Axios interceptor handles the 401 → refresh → retry cycle transparently.

---

## Error Handling Strategy

All API errors have the shape `{ error: string, code: string }`. Components extract `error.response.data.error` for display. The Axios interceptor does NOT swallow errors — it only handles the 401 refresh cycle. All other errors propagate to the component.

Specific error code handling:

| Code | Where handled | Message shown |
|---|---|---|
| `VALIDATION_ERROR` | Form component | Field-level message from `error.response.data.error` |
| `INVALID_CREDENTIALS` | LoginForm | "Invalid email or password." |
| `EMAIL_EXISTS` | RegisterForm | "An account with this email already exists." |
| `FILE_TOO_LARGE` | UploadForm | "File size must not exceed 5 MB." |
| `UNSUPPORTED_MEDIA_TYPE` | UploadForm | "Only PDF files are accepted." |
| `PROCESSING_FAILED` | ResultsPage / UploadForm | `error.response.data.error` (the reason string) |
| `NOT_FOUND` | ResultsPage | "Resume not found." |
| `FORBIDDEN` | ResultsPage | "You do not have permission to view this resume." |
| `INTERNAL_ERROR` | Any page | "Something went wrong. Please try again." |
| Network error | Any page | "Network error. Please check your connection." |

---

## Token Storage Strategy

| Item | Storage | Key |
|---|---|---|
| `accessToken` | `localStorage` | `kh_access` |
| `refreshToken` | `localStorage` | `kh_refresh` |
| `userEmail` | `localStorage` | `kh_email` |

`localStorage` is used for persistence across page reloads. The Axios interceptor reads `kh_access` directly from `localStorage` (not from React state) to avoid stale closure issues.

On logout, all three keys are removed.

---

## Scalability for Future Modules

The following patterns make adding new modules straightforward:

1. **New module = new service file** — `api/advisorService.js`, `api/chatbotService.js`, etc. All use the same `axiosClient`.
2. **New module = new page files** — `pages/AdvisorPage.jsx`, etc. Added to the route tree under `ProtectedRoute`.
3. **New module = new component directory** — `components/advisor/`, `components/chatbot/`, etc.
4. **No changes needed** to `AuthContext`, `axiosClient`, `Navbar` (add a nav link), or `ProtectedRoute`.
5. **Navbar** will receive new nav links per module. It reads an array of nav items so adding a module is a one-line array addition.

---

## Environment Variables

```
# .env.example
VITE_API_BASE_URL=http://127.0.0.1:8000
```

In production, `VITE_API_BASE_URL` points to the deployed backend domain.

---

## Dependencies

| Package | Purpose |
|---|---|
| `react` + `react-dom` | UI framework |
| `vite` | Build tool and dev server |
| `react-router-dom` | Client-side routing |
| `axios` | HTTP client with interceptor support |

No component library (Tailwind or plain CSS). No Redux. No Zustand for the initial milestone.
