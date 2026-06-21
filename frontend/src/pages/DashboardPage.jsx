/**
 * Dashboard — authenticated home page.
 * Shows stats (total uploads, best score) and quick-action cards.
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { listResumes } from '../api/resumeService'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorMessage }   from '../components/common/ErrorMessage'

export function DashboardPage() {
  const { userEmail } = useAuth()
  const navigate = useNavigate()

  const [totalCount, setTotalCount]   = useState(0)
  const [bestScore, setBestScore]     = useState(null)
  const [isLoading, setIsLoading]     = useState(true)
  const [error, setError]             = useState('')

  useEffect(() => {
    listResumes({ page: 1, page_size: 50 })
      .then(data => {
        setTotalCount(data.total_count)
        const scored = data.results
          .map(r => r.ats_score)
          .filter(s => s !== null && s !== undefined)
        setBestScore(scored.length > 0 ? Math.max(...scored) : null)
      })
      .catch(() => setError('Could not load your data. Please refresh.'))
      .finally(() => setIsLoading(false))
  }, [])

  if (isLoading) return <LoadingSpinner fullPage />

  return (
    <div className="dashboard">
      <h1 className="dashboard__welcome">
        Welcome back, <span className="dashboard__email">{userEmail}</span>
      </h1>

      <ErrorMessage message={error} onDismiss={() => setError('')} />

      {totalCount === 0 ? (
        // Empty state
        <div className="dashboard__empty">
          <p>You haven't uploaded any resumes yet.</p>
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => navigate('/upload')}
          >
            Upload your first resume
          </button>
        </div>
      ) : (
        <>
          {/* Stats */}
          <div className="dashboard__stats">
            <div className="stat-card">
              <span className="stat-card__value">{totalCount}</span>
              <span className="stat-card__label">Total Analyses</span>
            </div>
            <div className="stat-card">
              <span className="stat-card__value">
                {bestScore !== null ? bestScore : '—'}
              </span>
              <span className="stat-card__label">Best ATS Score</span>
            </div>
          </div>

          {/* Quick actions */}
          <div className="dashboard__actions">
            <div
              className="action-card"
              onClick={() => navigate('/upload')}
              role="button"
              tabIndex={0}
              onKeyDown={e => e.key === 'Enter' && navigate('/upload')}
            >
              <span className="action-card__icon">📤</span>
              <h3 className="action-card__title">Analyze a Resume</h3>
              <p className="action-card__desc">Upload a PDF and get instant feedback</p>
            </div>
            <div
              className="action-card"
              onClick={() => navigate('/history')}
              role="button"
              tabIndex={0}
              onKeyDown={e => e.key === 'Enter' && navigate('/history')}
            >
              <span className="action-card__icon">📋</span>
              <h3 className="action-card__title">View History</h3>
              <p className="action-card__desc">Browse all your past analyses</p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
