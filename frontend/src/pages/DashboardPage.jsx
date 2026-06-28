/**
 * Dashboard — authenticated home page.
 * Shows stats (total uploads, best score, career queries) and quick-action cards,
 * alongside recent resume analyses.
 */
import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { listResumes } from '../api/resumeService'
import { getAdviceHistory } from '../api/careerAdvisorService'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorMessage }   from '../components/common/ErrorMessage'

export function DashboardPage() {
  const { userEmail } = useAuth()
  const navigate = useNavigate()

  const [totalCount, setTotalCount]   = useState(0)
  const [bestScore, setBestScore]     = useState(null)
  const [recentResumes, setRecentResumes] = useState([])
  const [totalAdvice, setTotalAdvice] = useState(0)
  const [isLoading, setIsLoading]     = useState(true)
  const [error, setError]             = useState('')

  useEffect(() => {
    setIsLoading(true)
    setError('')

    // Aggregate statistics across resumes and career advisor queries
    Promise.all([
      listResumes({ page: 1, page_size: 50 }),
      getAdviceHistory({ page: 1, page_size: 1 })
    ])
      .then(([resumeData, adviceData]) => {
        setTotalCount(resumeData.total_count)
        setRecentResumes(resumeData.results.slice(0, 3))
        
        const scored = resumeData.results
          .map(r => r.ats_score)
          .filter(s => s !== null && s !== undefined)
        setBestScore(scored.length > 0 ? Math.max(...scored) : null)

        setTotalAdvice(adviceData.total_count)
      })
      .catch(() => setError('Could not load your dashboard data. Please refresh.'))
      .finally(() => setIsLoading(false))
  }, [])

  if (isLoading) return <LoadingSpinner fullPage />

  // Helper for ATS score status classes
  function getScoreClass(score) {
    if (score >= 70) return 'status-green'
    if (score >= 50) return 'status-yellow'
    return 'status-red'
  }

  return (
    <div className="dashboard page-container">
      {/* Hero Welcome Banner */}
      <div className="dashboard-hero">
        <div className="dashboard-hero__content">
          <h1 className="dashboard-hero__title">
            Welcome back, <span className="user-highlight">{userEmail ? userEmail.split('@')[0] : 'User'}</span>!
          </h1>
          <p className="dashboard-hero__subtitle">
            Analyze your resume's ATS performance, generate custom career roadmaps, and track your transition action plans.
          </p>
        </div>
      </div>

      <ErrorMessage message={error} onDismiss={() => setError('')} />

      {totalCount === 0 && totalAdvice === 0 ? (
        // Completely empty state
        <div className="dashboard__empty card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>🚀</span>
          <h2 style={{ marginBottom: '0.5rem', fontWeight: 700 }}>Get Started with Khan IntelliHub</h2>
          <p style={{ color: 'var(--color-muted)', marginBottom: '1.5rem', maxWidth: '480px', margin: '0 auto 1.5rem auto' }}>
            Upload your resume to get instant ATS feedback or setup a manual profile to explore tailored career advice.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button
              type="button"
              className="btn btn--primary"
              onClick={() => navigate('/upload')}
            >
              Analyze Resume
            </button>
            <button
              type="button"
              className="btn btn--secondary"
              onClick={() => navigate('/career-advisor')}
            >
              AI Career Advisor
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Aggregated Key Metrics Row */}
          <div className="dashboard__stats">
            <div className="stat-card">
              <div className="stat-card__icon">📄</div>
              <div className="stat-card__info">
                <span className="stat-card__value">{totalCount}</span>
                <span className="stat-card__label">Total Analyses</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-card__icon stat-card__icon--green">⭐️</div>
              <div className="stat-card__info">
                <span className="stat-card__value">
                  {bestScore !== null ? `${bestScore}%` : '—'}
                </span>
                <span className="stat-card__label">Best ATS Score</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-card__icon stat-card__icon--cyan">🎯</div>
              <div className="stat-card__info">
                <span className="stat-card__value">{totalAdvice}</span>
                <span className="stat-card__label">Career Plans</span>
              </div>
            </div>
          </div>

          {/* Two Column Layout */}
          <div className="dashboard-layout">
            
            {/* Left Column: Quick Actions */}
            <div className="dashboard-main-col">
              <h2 className="section-heading" style={{ marginTop: 0, marginBottom: '1rem' }}>Quick Actions</h2>
              <div className="dashboard__actions">
                <div
                  className="action-card"
                  onClick={() => navigate('/upload')}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && navigate('/upload')}
                >
                  <div className="action-card__icon">📤</div>
                  <div className="action-card__body">
                    <h3 className="action-card__title">Analyze a Resume</h3>
                    <p className="action-card__desc">Upload a PDF resume and get an instant ATS scoring and feedback report</p>
                  </div>
                  <span className="action-card__arrow">→</span>
                </div>

                <div
                  className="action-card"
                  onClick={() => navigate('/career-advisor')}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && navigate('/career-advisor')}
                >
                  <div className="action-card__icon">🤖</div>
                  <div className="action-card__body">
                    <h3 className="action-card__title">AI Career Advisor</h3>
                    <p className="action-card__desc">Generate custom roadmaps, salary insights, checklists, and job matching</p>
                  </div>
                  <span className="action-card__arrow">→</span>
                </div>

                <div
                  className="action-card"
                  onClick={() => navigate('/history')}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && navigate('/history')}
                >
                  <div className="action-card__icon">📋</div>
                  <div className="action-card__body">
                    <h3 className="action-card__title">System History</h3>
                    <p className="action-card__desc">Browse all your past resume scores and career recommendation roadmaps</p>
                  </div>
                  <span className="action-card__arrow">→</span>
                </div>
              </div>
            </div>

            {/* Right Column: Recent Resumes Uploads */}
            <div className="dashboard-sidebar-col">
              <div className="card recent-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border)', paddingBottom: '0.75rem', marginBottom: '0.5rem' }}>
                  <h2 className="section-title" style={{ fontSize: '1.2rem', margin: 0 }}>Recent Resumes</h2>
                  <Link to="/history" style={{ fontSize: '0.85rem', fontWeight: 600 }}>See All</Link>
                </div>
                
                {recentResumes.length === 0 ? (
                  <div style={{ padding: '2rem 1rem', textAlign: 'center', color: 'var(--color-muted)', fontSize: '0.9rem' }}>
                    No resumes analyzed yet.
                  </div>
                ) : (
                  <div className="recent-list">
                    {recentResumes.map(resume => (
                      <div key={resume.resume_id} className="recent-item">
                        <div className="recent-item__info">
                          <h4 className="recent-item__title" title={resume.original_filename}>
                            {resume.original_filename}
                          </h4>
                          <span className="recent-item__meta">
                            {new Date(resume.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        {resume.ats_score !== null && (
                          <div className={`recent-item__score-badge ${getScoreClass(resume.ats_score)}`}>
                            {resume.ats_score}%
                          </div>
                        )}
                        <button
                          type="button"
                          className="btn btn--secondary btn--sm"
                          style={{ marginLeft: '0.5rem', padding: '0.3rem 0.6rem' }}
                          onClick={() => navigate(`/results/${resume.resume_id}`)}
                        >
                          View
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

          </div>
        </>
      )}
    </div>
  )
}
