# Khan IntelliHub — Frontend Implementation Tasks
## Milestone 6: Resume Analyzer React + Vite SPA

---

## Overview

Implement the Khan IntelliHub frontend in seven sequential tasks. Each task produces independently testable output before the next begins. The stack is React 18 + Vite 5 + React Router v6 + Axios. No Redux. No component library.

---

## Task Dependency Order

```
Task 1 (scaffold + Axios client)
    └── Task 2 (AuthContext + routing skeleton)
            └── Task 3 (auth pages: login, register)
                    └── Task 4 (dashboard + navbar)
                            └── Task 5 (upload page)
                                    └── Task 6 (results page)
                                            └── Task 7 (history page + delete)
```

---

## Tasks

---

### Task 1 — Project Scaffold and Axios Client

**Goal:** A running Vite dev server with the folder structure in place and a working Axios client that handles JWT injection and token refresh.

**Steps:**

1. Inside the repo root, run:
   ```
   npm create vite@latest frontend -- --template react
   cd frontend
   npm install
   npm install axios react-router-dom
   ```

2. Delete the boilerplate: clear `src/App.jsx`, `src/App.css`, `src/index.css` content (keep the files, wipe their content).

3. Create the folder structure:
   ```
   src/api/
   src/context/
   src/hooks/
   src/components/common/
   src/components/auth/
   src/components/resume/
   src/pages/
   src/utils/
   ```

4. Create `frontend/.env.example`:
   ```
   VITE_API_BASE_URL=http://127.0.0.1:8000
   ```

5. Create `frontend/.env` (gitignored):
   ```
   VITE_API_BASE_URL=http://127.0.0.1:8000
   ```

6. Add `frontend/.env` to `.gitignore` (add a `frontend/.env*` rule; `.env.example` must still be committed).

7. Implement `src/api/axiosClient.js`:
   - Creates an Axios instance with `baseURL: import.meta.env.VITE_API_BASE_URL`
   - Request interceptor: reads `localStorage.getItem('kh_access')`, adds `Authorization: Bearer <token>` if present
   - Response interceptor: on 401, reads `localStorage.getItem('kh_refresh')`, calls `POST /api/v1/auth/token/refresh/`, on success stores new access token and retries; on failure clears `kh_access`, `kh_refresh`, `kh_email` from localStorage and calls `window.location.href = '/login'`
   - Uses a `_retry` flag on the config to prevent infinite retry loops

8. Implement `src/api/authService.js`:
   - `register(email, password)` → `POST /api/v1/auth/register/`
   - `login(email, password)` → `POST /api/v1/auth/login/`
   - `refreshToken(refresh)` → `POST /api/v1/auth/token/refresh/`

9. Implement `src/api/resumeService.js`:
   - `uploadResume(file, jobDescription)` → `POST /api/v1/resumes/upload/` as `multipart/form-data`
   - `listResumes({ page, page_size })` → `GET /api/v1/resumes/`
   - `getResults(resumeId)` → `GET /api/v1/resumes/${resumeId}/results/`
   - `deleteResume(resumeId)` → `DELETE /api/v1/resumes/${resumeId}/`

10. Implement `src/utils/formatters.js`:
    - `formatDate(isoString)` → returns readable date string (e.g. "15 Jun 2025")
    - `getStatusLabel(status)` → returns display string (e.g. `COMPLETED` → "Completed")
    - `getStatusColor(status)` → returns CSS class name or colour string by tier
    - `getScoreColor(score)` → returns colour by score tier (0-39 red, 40-59 orange, 60-79 yellow, 80-100 green)

11. Implement `src/utils/validators.js`:
    - `isValidEmail(email)` → boolean
    - `isValidPassword(password)` → boolean (length >= 8)

**Acceptance check:** `npm run dev` starts without errors. The Axios client module imports cleanly. No browser errors on a blank page load.

---

### Task 2 — AuthContext, Routing Skeleton, and Common Components

**Goal:** Authentication state flows through the app; all routes are defined; protected and public routes work; the Navbar renders on authenticated pages.

**Steps:**

1. Implement `src/context/AuthContext.jsx`:
   - On mount, reads `kh_access`, `kh_refresh`, `kh_email` from localStorage to restore session
   - Exposes `{ accessToken, refreshToken, userEmail, isAuthenticated, login, logout, setAccessToken }`
   - `login(access, refresh, email)` stores all three in localStorage and state
   - `logout()` removes all three from localStorage and resets state to null
   - `setAccessToken(token)` updates access token in localStorage and state (used by Axios interceptor after silent refresh)

2. Implement `src/hooks/useAuth.js`:
   ```js
   import { useContext } from 'react'
   import { AuthContext } from '../context/AuthContext'
   export function useAuth() { return useContext(AuthContext) }
   ```

3. Implement `src/components/common/ProtectedRoute.jsx`:
   - Reads `isAuthenticated` from `useAuth()`
   - If false: `<Navigate to={/login?next=${location.pathname}} replace />`
   - If true: `<Outlet />`

4. Implement `src/components/common/PublicRoute.jsx`:
   - Reads `isAuthenticated` from `useAuth()`
   - If true: `<Navigate to="/dashboard" replace />`
   - If false: `<Outlet />`

5. Implement `src/components/common/LoadingSpinner.jsx`:
   - Accepts optional `fullPage` boolean prop
   - `fullPage=true` → centres spinner on the screen
   - `fullPage=false` (default) → inline spinner

6. Implement `src/components/common/ErrorMessage.jsx`:
   - Props: `message` (string), `onDismiss` (optional function)
   - Renders a styled error banner; if `onDismiss` provided, shows an × button

7. Implement `src/components/common/ConfirmDialog.jsx`:
   - Props: `isOpen`, `message`, `onConfirm`, `onCancel`, `isLoading`
   - Modal overlay with message, Confirm button (disabled when `isLoading`), Cancel button

8. Implement `src/components/common/Navbar.jsx`:
   - Only renders when `isAuthenticated` is true
   - Shows brand name, links to `/dashboard`, `/upload`, `/history`
   - Shows `userEmail` from `useAuth()`
   - Logout button calls `logout()` then `navigate('/')`

9. Wire `App.jsx`:
   ```jsx
   <AuthProvider>
     <BrowserRouter>
       <Routes>
         {/* Public — redirects authed users away */}
         <Route element={<PublicRoute />}>
           <Route path="/" element={<LandingPage />} />
           <Route path="/login" element={<LoginPage />} />
           <Route path="/register" element={<RegisterPage />} />
         </Route>
         {/* Protected — redirects unauthed users to login */}
         <Route element={<><Navbar /><ProtectedRoute /></>}>
           <Route path="/dashboard" element={<DashboardPage />} />
           <Route path="/upload" element={<UploadPage />} />
           <Route path="/results/:resumeId" element={<ResultsPage />} />
           <Route path="/history" element={<HistoryPage />} />
         </Route>
       </Routes>
     </BrowserRouter>
   </AuthProvider>
   ```
   All page components can be empty stubs at this stage.

**Acceptance check:**
- Visiting `/dashboard` without auth redirects to `/login?next=/dashboard`
- Visiting `/login` while authenticated redirects to `/dashboard`
- Navbar renders on `/dashboard` but not on `/` or `/login`

---

### Task 3 — Authentication Pages

**Goal:** A user can register and log in through the UI. Errors display inline. After auth, tokens are stored and the user lands on `/dashboard`.

**Steps:**

1. Implement `src/components/auth/RegisterForm.jsx`:
   - Controlled fields: `email`, `password`
   - Client-side validation: email format check, password >= 8 chars — validated on submit before API call
   - Submit calls `authService.register(email, password)`
   - On 201: calls `login(access, refresh, email)` from `useAuth()`, navigates to `/dashboard`
   - On 409 (`EMAIL_EXISTS`): displays "An account with this email already exists."
   - On 400 (`VALIDATION_ERROR`): displays the error message from `response.data.error`
   - Loading state: submit button shows "Creating account..." and is disabled during request
   - Includes a link to `/login` ("Already have an account? Sign in")

2. Implement `src/components/auth/LoginForm.jsx`:
   - Controlled fields: `email`, `password`
   - Submit calls `authService.login(email, password)`
   - On 200: calls `login(access, refresh, email)` — note login endpoint does not return `user_id` or `email`, so extract email from the submitted form value
   - On 401 (`INVALID_CREDENTIALS`): displays "Invalid email or password."
   - On 400: displays validation error
   - Loading state during request
   - Includes a link to `/register`

3. Implement `src/pages/RegisterPage.jsx`:
   - Renders `<RegisterForm />`
   - Simple centred card layout

4. Implement `src/pages/LoginPage.jsx`:
   - Renders `<LoginForm />`
   - Reads `?next` param from URL; passes it to the form for post-login redirect
   - Simple centred card layout

**Acceptance check:**
- Register with a new email → lands on `/dashboard`
- Register with existing email → error displayed inline, no redirect
- Login with wrong password → error displayed inline
- Login with correct credentials → lands on `/dashboard` (or `?next` path)
- After login, Navbar shows the user's email

---

### Task 4 — Landing Page and Dashboard

**Goal:** The landing page explains the product to guests. The dashboard shows the user's stats and quick actions.

**Steps:**

1. Implement `src/pages/LandingPage.jsx`:
   - Hero section: headline "Khan IntelliHub", subtitle "AI-powered resume analysis", two buttons: "Get Started" (→ `/register`) and "Sign In" (→ `/login`)
   - Features section: three cards:
     - "Upload Your Resume" — "Submit a PDF and our pipeline extracts structured content instantly."
     - "Get Your ATS Score" — "Receive a 0–100 ATS compatibility score based on four weighted categories."
     - "Actionable Feedback" — "Get prioritised actions, section suggestions, and missing skills analysis."
   - No Navbar (landing is outside the protected layout)

2. Implement `src/pages/DashboardPage.jsx`:
   - On mount: calls `resumeService.listResumes({ page: 1, page_size: 50 })`
   - While loading: shows `<LoadingSpinner fullPage />`
   - On error: shows `<ErrorMessage>`
   - Computes from the results:
     - `totalCount` from `response.total_count`
     - `highestScore` — max of all `ats_score` values (filtering out nulls)
   - Renders:
     - Welcome heading: "Welcome back, {userEmail}"
     - Stat card: "Total Analyses" with `totalCount`
     - Stat card: "Best ATS Score" with `highestScore` (or "—" if no scored records)
     - Action card: "Analyze a Resume" → navigates to `/upload`
     - Action card: "View History" → navigates to `/history`
   - Empty state (totalCount === 0): replaces stat cards with "Upload your first resume to get started" and a single "Upload Now" button

**Acceptance check:**
- Landing page renders with both CTA buttons
- Dashboard shows correct total count and best score
- Empty state renders when user has no resumes
- Clicking action cards navigates correctly

---

### Task 5 — Resume Upload Page

**Goal:** A user can upload a PDF resume with optional job description and is redirected to the results page on success.

**Steps:**

1. Implement `src/components/resume/UploadForm.jsx`:

   Internal state: `selectedFile`, `jobDescription`, `isLoading`, `error`

   File selection:
   - A visible drag-and-drop zone that accepts `application/pdf` only
   - File input (`accept=".pdf"`) hidden behind a "Browse Files" button
   - HTML5 drag events on the drop zone: `onDragOver` (prevents default), `onDrop` (reads `event.dataTransfer.files[0]`)
   - On file selected/dropped: stores the `File` object in `selectedFile`, displays the filename
   - A "Remove" link clears the selection

   Job Description:
   - `<textarea>` labelled "Job Description (optional)"
   - Placeholder: "Paste the job description here to tailor your ATS score..."
   - `maxLength={10000}`

   Submission:
   - Submit button disabled if `!selectedFile || isLoading`
   - On submit: sets `isLoading = true`, clears `error`
   - Builds `FormData`: appends `file` and optionally `job_description`
   - Calls `resumeService.uploadResume(file, jobDescription)`
   - On 202: calls `onSuccess(data.resume_id)`
   - On 413: sets `error = "File size must not exceed 5 MB."`
   - On 415: sets `error = "Only PDF files are accepted."`
   - On 422: sets `error = response.data.error`
   - On any other error: sets `error = "Something went wrong. Please try again."`
   - Always: sets `isLoading = false`

   Renders `<ErrorMessage>` if `error` is set.

2. Implement `src/pages/UploadPage.jsx`:
   - Renders `<UploadForm onSuccess={(resumeId) => navigate(/results/${resumeId})} />`

**Acceptance check:**
- Drop zone highlights on drag-over
- Selecting a file shows the filename
- Submitting with a valid PDF navigates to `/results/:resumeId`
- Submitting a non-PDF file (tested by renaming a PNG to .pdf — backend will reject) shows the 415 error message
- Loading state appears during upload; submit button is disabled

---

### Task 6 — Results Page

**Goal:** The full ATS analysis for a resume is displayed clearly with score, sub-scores, and all feedback sections.

**Steps:**

1. Implement `src/components/resume/ScoreGauge.jsx`:
   - Props: `score` (0–100)
   - Renders the score as a large centred number
   - Surrounds it with a circular SVG arc that fills proportionally to the score
   - Arc colour determined by `getScoreColor(score)` from `formatters.js`
   - Label below the number: "ATS Score"

2. Implement `src/components/resume/ScoreBreakdown.jsx`:
   - Props: `scores` `{ skills_match, section_completeness, experience_quality, content_quality }`
   - Renders four rows. Each row: label, weight, horizontal progress bar, numeric value
   - Labels and weights:
     - Skills Match — 40%
     - Section Completeness — 20%
     - Experience Quality — 20%
     - Content Quality — 20%
   - Progress bar width = `score%` of its container

3. Implement `src/components/resume/PriorityActions.jsx`:
   - Props: `actions` array of `{ priority, action }`
   - Groups by `priority` into three sections: High, Medium, Low
   - Each group is a collapsible `<details>` element (open by default for "high")
   - Each action card has a coloured left border: high=red, medium=amber, low=grey
   - If a priority group is empty, it is not rendered

4. Implement `src/components/resume/SectionSuggestions.jsx`:
   - Props: `suggestions` `{ contact, skills, education, experience, projects, certifications }`
   - Iterates over keys; renders a card only if value is non-null
   - Card heading = capitalised section name; card body = suggestion text

5. Implement `src/components/resume/MissingSkillsTags.jsx`:
   - Props: `skills` array of strings
   - Renders each as a pill tag
   - If `skills` is empty or null, renders nothing

6. Implement `src/components/resume/FeedbackSection.jsx`:
   - Props: `feedbackReport` object
   - Renders all sub-sections in this order:
     1. Overall Summary (`<p>` with the summary string)
     2. Top Strengths (bulleted list with ✓ icon)
     3. Top Weaknesses (bulleted list with ✗ icon)
     4. `<PriorityActions actions={feedbackReport.priority_actions} />`
     5. `<SectionSuggestions suggestions={feedbackReport.section_suggestions} />`
     6. Skills Suggestions (bulleted list, only if non-empty)
     7. Experience Suggestions (bulleted list, only if non-empty)
     8. Enhancement Tips (bulleted list, only if non-empty)
     9. `<MissingSkillsTags skills={feedbackReport.missing_skills} />`
   - Each sub-section has a heading

7. Implement `src/pages/ResultsPage.jsx`:
   - Reads `resumeId` from `useParams()`
   - On mount: calls `resumeService.getResults(resumeId)`
   - State: `isLoading`, `data`, `error`
   - While loading: `<LoadingSpinner fullPage />`
   - On error:
     - 404 → "Resume not found."
     - 403 → "You do not have permission to view this resume."
     - 422 → displays `error.response.data.error`
     - Other → "Something went wrong. Please try again."
   - On success: renders:
     - `<ScoreGauge score={data.ats_score} />`
     - `<ScoreBreakdown scores={data.scores} />`
     - `<FeedbackSection feedbackReport={data.feedback_report} />`
     - "← Back to History" link → `/history`

**Acceptance check:**
- Navigate to `/results/:id` after upload → full results display with score and feedback
- Score gauge shows correct colour for the score tier
- Priority actions grouped by level
- Section suggestions only show non-null sections
- Missing skills render as tags
- Navigating to a non-existent resume_id shows "Resume not found."

---

### Task 7 — History Page and Delete

**Goal:** Users can browse their resume history with pagination and delete individual resumes with confirmation.

**Steps:**

1. Implement `src/hooks/useResumes.js`:
   ```js
   function useResumes(page, pageSize = 10) {
     const [data, setData] = useState(null)
     const [isLoading, setIsLoading] = useState(true)
     const [error, setError] = useState(null)

     useEffect(() => {
       setIsLoading(true)
       resumeService.listResumes({ page, page_size: pageSize })
         .then(res => setData(res))
         .catch(err => setError(err))
         .finally(() => setIsLoading(false))
     }, [page, pageSize])

     return { data, isLoading, error }
   }
   ```

2. Implement `src/components/resume/HistoryTable.jsx`:
   - Props: `records`, `totalCount`, `page`, `pageSize`, `onPageChange(newPage)`, `onDelete(resumeId)`, `deletingId`
   - Renders a `<table>` with columns: Filename, Uploaded, Status, ATS Score, Actions
   - `formatDate` from `formatters.js` for upload date
   - Status badge: uses `getStatusColor` and `getStatusLabel` from `formatters.js`
   - ATS Score: shows the integer or "—" if null
   - Actions column: "View" button (→ `/results/:resumeId`) and "Delete" button
   - Delete button shows a loading indicator when `deletingId === record.resume_id`
   - Pagination row below table:
     - Previous button (disabled when `page === 1`)
     - "Page {page} of {Math.ceil(totalCount / pageSize)}" text
     - Next button (disabled when on last page)
   - Empty state: "No resumes yet. Upload your first resume." with a link to `/upload`

3. Implement `src/pages/HistoryPage.jsx`:
   - State: `page` (starts at 1), `records`, `totalCount`, `isLoading`, `error`, `deletingId`, `dialogOpen`, `selectedResumeId`
   - On mount and `page` change: fetches from `resumeService.listResumes({ page, page_size: 10 })`
   - Delete flow:
     1. User clicks Delete on a row → sets `selectedResumeId = resumeId`, `dialogOpen = true`
     2. User confirms in `ConfirmDialog` → sets `deletingId = selectedResumeId`, calls `resumeService.deleteResume(selectedResumeId)`
     3. On 204: removes record from `records` array in local state, decrements `totalCount`, closes dialog, clears `deletingId` and `selectedResumeId`
     4. On error: shows `<ErrorMessage>`, clears `deletingId`
     5. User cancels → closes dialog, clears `selectedResumeId`
   - Renders:
     - `<LoadingSpinner fullPage />` while loading
     - `<ErrorMessage>` on fetch error
     - `<HistoryTable>` with all props wired
     - `<ConfirmDialog isOpen={dialogOpen} message="Are you sure you want to delete this resume? This cannot be undone." onConfirm={handleConfirmDelete} onCancel={handleCancelDelete} isLoading={!!deletingId} />`

**Acceptance check:**
- History page loads and shows all resumes with correct status badges
- Pagination works: clicking Next increments page, Previous decrements
- Clicking "View" navigates to `/results/:resumeId`
- Clicking "Delete" opens the confirmation dialog
- Cancelling the dialog does not delete anything
- Confirming deletes the record and removes it from the table immediately
- Empty state shows when no resumes exist
- After deleting the last item on page 2, the page count updates correctly

---

## Definition of Done

Milestone 6 is complete when:

- [ ] `npm run dev` starts the frontend and all seven pages render without console errors
- [ ] Register flow works end-to-end against the live backend
- [ ] Login flow works with token refresh on expiry
- [ ] Protected routes redirect unauthenticated users to login
- [ ] Public routes redirect authenticated users to dashboard
- [ ] Dashboard shows real data from the API
- [ ] Upload flow accepts a real PDF and displays results
- [ ] Results page displays ATS score, category scores, and all feedback sections
- [ ] History page loads paginated data and pagination controls work
- [ ] Delete flow shows confirmation dialog and removes the record on confirm
- [ ] All error states display readable messages (no raw JSON in the UI)
- [ ] Token refresh happens silently when the access token expires mid-session
- [ ] `npm run build` produces a production bundle without errors
- [ ] No secrets or tokens appear in committed files

---

## Notes

- Tasks 1 and 2 are the critical foundation — do not skip steps in them
- The Axios interceptor in Task 1 is the single most important piece of the architecture; get it right before building any pages
- No component library is used; all styling is plain CSS or inline styles
- The backend is already running at `http://127.0.0.1:8000` with `python manage.py runserver`
- CORS is already configured on the backend to allow `http://localhost:5173`
- The Vite dev server runs on port 5173 by default
