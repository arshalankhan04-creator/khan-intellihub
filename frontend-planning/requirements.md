# Khan IntelliHub — Frontend Requirements
## Milestone 6: Resume Analyzer React + Vite SPA

---

## Introduction

This document defines the functional and non-functional requirements for the Khan IntelliHub frontend. The frontend is a React + Vite single-page application that consumes the existing Django REST Framework backend (Milestones 1–5, 191/191 tests passing).

The architecture must be designed from the start to accommodate future Khan IntelliHub modules — AI Career Advisor, PDF Chatbot, Notes Summarizer, Interview Preparation Tool, and Smart Business Intelligence Tool — without requiring structural rewrites.

---

## Glossary

- **Guest** — an unauthenticated visitor to the SPA
- **User** — an authenticated individual with a valid JWT session
- **Access Token** — a short-lived JWT (60 min) stored in memory or localStorage, sent in every API request header
- **Refresh Token** — a long-lived JWT (7 days) used to obtain new access tokens silently
- **Protected Route** — a route that redirects unauthenticated users to `/login`
- **Public Route** — a route accessible without authentication; redirects authenticated users away from login/register
- **ATS Score** — integer 0–100 returned by the backend pipeline
- **Feedback Report** — structured JSON object containing overall_summary, top_strengths, top_weaknesses, priority_actions, section_suggestions, skills_suggestions, experience_suggestions, enhancement_tips, missing_skills
- **Resume Record** — a single upload with its analysis results, identified by `resume_id` (UUID)

---

## Requirement 1: Authentication

### 1.1 Registration

- WHEN a Guest visits `/register`, the page SHALL display a registration form with email and password fields
- WHEN a Guest submits valid credentials, the frontend SHALL call `POST /api/v1/auth/register/`, store the returned `access` and `refresh` tokens, and redirect to `/dashboard`
- WHEN the backend returns HTTP 409 (`EMAIL_EXISTS`), the form SHALL display the message "An account with this email already exists"
- WHEN the backend returns HTTP 400 (`VALIDATION_ERROR`), the form SHALL display the specific validation error inline
- Password field SHALL enforce minimum 8 characters with a client-side validation message before submission
- IF a User is already authenticated and visits `/register`, they SHALL be redirected to `/dashboard`

### 1.2 Login

- WHEN a Guest visits `/login`, the page SHALL display a login form with email and password fields
- WHEN a Guest submits valid credentials, the frontend SHALL call `POST /api/v1/auth/login/`, store tokens, and redirect to `/dashboard` (or the originally requested protected route)
- WHEN the backend returns HTTP 401 (`INVALID_CREDENTIALS`), the form SHALL display "Invalid email or password"
- IF a User is already authenticated and visits `/login`, they SHALL be redirected to `/dashboard`

### 1.3 Token Management

- The access token SHALL be sent exclusively in the `Authorization: Bearer <token>` header on every API request
- Tokens SHALL never be included in URL query parameters
- WHEN any API request returns HTTP 401, the frontend SHALL automatically attempt one silent token refresh via `POST /api/v1/auth/token/refresh/` before retrying the original request
- IF the refresh attempt fails (expired or invalid refresh token), the frontend SHALL clear all stored tokens and redirect the user to `/login`
- The refresh token SHALL be stored in `localStorage`; the access token MAY be stored in memory or `localStorage`

### 1.4 Logout

- WHEN a User clicks Logout, the frontend SHALL clear all stored tokens and redirect to `/`
- After logout, attempting to access any protected route SHALL redirect to `/login`

---

## Requirement 2: Protected and Public Routes

- All routes under `/dashboard`, `/upload`, `/results/:resumeId`, and `/history` SHALL require authentication
- WHEN an unauthenticated user attempts to access a protected route, they SHALL be redirected to `/login` with the original path preserved as a `next` query parameter
- After successful login, the user SHALL be redirected to the originally requested path
- Routes `/`, `/login`, and `/register` SHALL be accessible to unauthenticated users
- Authenticated users visiting `/login` or `/register` SHALL be redirected to `/dashboard`

---

## Requirement 3: Landing Page

- The landing page at `/` SHALL be accessible to all visitors without authentication
- It SHALL describe what Khan IntelliHub does and the Resume Analyzer module specifically
- It SHALL display clear calls to action: "Register" and "Login"
- It SHALL present the core value proposition: upload resume → get ATS score → get actionable feedback

---

## Requirement 4: Dashboard

- WHEN an authenticated User visits `/dashboard`, the page SHALL display a personalised welcome message using their email address
- The dashboard SHALL show a summary count of total resumes uploaded by the User
- The dashboard SHALL show the highest ATS score achieved across all the User's resumes (or a prompt to upload if none exist)
- The dashboard SHALL provide quick-action navigation cards to the Upload page and History page
- IF the User has no resume records, the dashboard SHALL show an empty state with a prompt to upload their first resume

---

## Requirement 5: Resume Upload

- WHEN a User visits `/upload`, the page SHALL display a file upload area that accepts PDF files only
- The upload area SHALL support both drag-and-drop and click-to-browse file selection
- The selected file name SHALL be displayed before submission
- An optional Job Description textarea SHALL be provided below the file selector
- WHEN the User submits, the frontend SHALL display a loading state (spinner, disabled submit button) for the duration of the API call
- The upload call SHALL use `multipart/form-data` with fields `file` and optionally `job_description`
- WHEN the backend returns HTTP 202 (`COMPLETED`), the frontend SHALL navigate to `/results/:resumeId`
- WHEN the backend returns HTTP 413, the frontend SHALL display "File size must not exceed 5 MB" inline
- WHEN the backend returns HTTP 415, the frontend SHALL display "Only PDF files are accepted" inline
- WHEN the backend returns HTTP 422, the frontend SHALL display the error reason from the response inline
- The submit button SHALL be disabled while a file has not been selected

---

## Requirement 6: ATS Results Display

- WHEN a User visits `/results/:resumeId`, the page SHALL call `GET /api/v1/resumes/:resumeId/results/` and display the full analysis
- The page SHALL display the ATS score (0–100) prominently as a visual gauge or large number
- The page SHALL display all four category scores:
  - Skills Match (40%)
  - Section Completeness (20%)
  - Experience Quality (20%)
  - Content Quality (20%)
- The page SHALL display the feedback report sections:
  - Overall Summary (the `overall_summary` string)
  - Top Strengths (the `top_strengths` list)
  - Top Weaknesses (the `top_weaknesses` list)
  - Priority Actions (the `priority_actions` list, grouped by priority: high / medium / low)
  - Section Suggestions (one card per resume section, only shown if suggestion is non-null)
  - Skills Suggestions (the `skills_suggestions` list)
  - Experience Suggestions (the `experience_suggestions` list)
  - Enhancement Tips (the `enhancement_tips` list)
  - Missing Skills (the `missing_skills` list as tags)
- WHEN the record status is `PARSE_FAILED`, `SCORE_FAILED`, or `FEEDBACK_FAILED`, the page SHALL display the `error_reason` from the response
- The page SHALL include a "Back to History" navigation link
- WHEN the record is not found (404) or the User does not own it (403), the page SHALL display an appropriate error message

---

## Requirement 7: Resume History

- WHEN a User visits `/history`, the page SHALL call `GET /api/v1/resumes/` and display a paginated table of the User's resumes
- Each row SHALL display: filename, upload date, status badge (colour-coded), ATS score (or dash if null), and a "View Results" link
- Status badge colours:
  - `COMPLETED` → green
  - `PENDING`, `PARSED`, `SCORED` → yellow
  - `PARSE_FAILED`, `SCORE_FAILED`, `FEEDBACK_FAILED` → red
- The page SHALL support pagination with Previous / Next controls
- The default page size SHALL be 10
- WHEN there are no resumes, the page SHALL display an empty state with a link to the Upload page
- Each row SHALL include a Delete button

---

## Requirement 8: Resume Deletion

- WHEN a User clicks Delete on a resume row, the frontend SHALL display a confirmation dialog ("Are you sure you want to delete this resume? This cannot be undone.")
- WHEN the User confirms, the frontend SHALL call `DELETE /api/v1/resumes/:resumeId/`
- WHEN the backend returns HTTP 204, the frontend SHALL remove the row from the list without a page reload
- WHEN the backend returns HTTP 500, the frontend SHALL display "Failed to delete the file. Please try again."
- The Delete action SHALL show a loading state on the button while the request is in flight

---

## Requirement 9: Loading States

- EVERY API call SHALL display a visual loading indicator while awaiting a response
- Form submission buttons SHALL be disabled during submission
- Full-page loading states SHALL be used for initial page data fetches
- Inline loading states SHALL be used for actions on existing elements (e.g., delete button)

---

## Requirement 10: Error Handling

- ALL API error responses SHALL be surfaced to the user with a readable message — never a raw JSON dump
- Network errors (no connectivity) SHALL display "Network error. Please check your connection."
- Unexpected server errors (HTTP 500) SHALL display "Something went wrong. Please try again."
- Error messages SHALL appear inline near the relevant action (not as browser alerts)
- Errors SHALL be dismissible by the user

---

## Requirement 11: Architecture Scalability for Future Modules

- ALL API communication SHALL go through a single centralised Axios client instance
- Authentication state SHALL be managed in a single context/store accessible to all modules
- Route structure SHALL be designed to accommodate new module routes (e.g., `/advisor`, `/chatbot`, `/notes`, `/interview`) without refactoring existing routes
- Shared UI components (Navbar, LoadingSpinner, ProtectedRoute, error states) SHALL live in a `components/common/` directory and be module-agnostic
- Per-module API service files SHALL be isolated (e.g., `api/resumeService.js`, future `api/advisorService.js`)
- Per-module pages SHALL be isolated in a `pages/` directory
- Per-module components SHALL be isolated in `components/<module>/` subdirectories

---

## Requirement 12: Non-Functional Requirements

- The SPA SHALL be built with React 18+ and Vite 5+
- State management SHALL use React Context API for authentication; component-level `useState` for local UI state; no Redux unless a clear need arises
- The frontend SHALL communicate with the backend exclusively over the base URL configured in `VITE_API_BASE_URL` environment variable
- The `.env` file SHALL be gitignored; a `.env.example` SHALL document required variables
- All forms SHALL implement both client-side validation (before submission) and server-side error display (after response)
- The application SHALL be fully navigable via the browser back/forward buttons
- No sensitive tokens SHALL appear in URLs or browser history
