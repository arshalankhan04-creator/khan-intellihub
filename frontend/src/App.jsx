/**
 * Root application component.
 * Wraps the entire app in AuthProvider and defines the route tree.
 *
 * Route structure:
 *   Public  (redirect authed users to /dashboard):
 *     /           → LandingPage
 *     /login      → LoginPage
 *     /register   → RegisterPage
 *
 *   Protected  (redirect unauthed users to /login?next=...):
 *     /dashboard          → DashboardPage
 *     /upload             → UploadPage
 *     /results/:resumeId  → ResultsPage
 *     /history            → HistoryPage
 */
import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/common/ProtectedRoute'
import { PublicRoute }    from './components/common/PublicRoute'
import { Navbar }         from './components/common/Navbar'

import { LandingPage }  from './pages/LandingPage'
import { LoginPage }    from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { DashboardPage } from './pages/DashboardPage'
import { UploadPage }   from './pages/UploadPage'
import { ResultsPage }  from './pages/ResultsPage'
import { HistoryPage }  from './pages/HistoryPage'
import { CareerAdvisorPage } from './pages/CareerAdvisorPage'
import { CareerResultsPage } from './pages/CareerResultsPage'

/** Layout wrapper for authenticated pages: Navbar above, content below. */
function AuthenticatedLayout() {
  return (
    <>
      <Navbar />
      <main className="main-content">
        <Outlet />
      </main>
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes — authenticated users are redirected away */}
          <Route element={<PublicRoute />}>
            <Route path="/"         element={<LandingPage />} />
            <Route path="/login"    element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>

          {/* Protected routes — unauthenticated users are redirected to login */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AuthenticatedLayout />}>
              <Route path="/dashboard"          element={<DashboardPage />} />
              <Route path="/upload"             element={<UploadPage />} />
              <Route path="/results/:resumeId"  element={<ResultsPage />} />
              <Route path="/history"            element={<HistoryPage />} />
              <Route path="/career-advisor"     element={<CareerAdvisorPage />} />
              <Route path="/career-advisor/:recordId" element={<CareerResultsPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
