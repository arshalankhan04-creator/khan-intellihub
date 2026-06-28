import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getAdviceResults } from '../api/careerAdvisorService'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorMessage } from '../components/common/ErrorMessage'

export function CareerResultsPage() {
  const { recordId } = useParams()
  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  
  // Interactive checklist state
  const [checkedItems, setCheckedItems] = useState({})

  useEffect(() => {
    setIsLoading(true)
    getAdviceResults(recordId)
      .then(res => {
        setData(res)
        // Initialize checked items from localstorage if available, else empty
        const saved = localStorage.getItem(`checklist_${recordId}`)
        if (saved) {
          setCheckedItems(JSON.parse(saved))
        }
      })
      .catch(err => {
        if (err.response?.status === 404) {
          setError('Career advice record not found.')
        } else if (err.response?.status === 403) {
          setError('You do not have permission to view this record.')
        } else {
          setError('Failed to fetch results. Please try again.')
        }
      })
      .finally(() => setIsLoading(false))
  }, [recordId])

  function handleToggleCheck(index) {
    const updated = {
      ...checkedItems,
      [index]: !checkedItems[index]
    }
    setCheckedItems(updated)
    localStorage.setItem(`checklist_${recordId}`, JSON.stringify(updated))
  }

  if (isLoading) return <LoadingSpinner fullPage />
  if (error) {
    return (
      <div className="page-container">
        <ErrorMessage message={error} />
        <Link to="/career-advisor" className="link back-link">← Back to Career Hub</Link>
      </div>
    )
  }

  if (!data) return null

  const { target_role, location, resume_filename, career_paths, salary_insights, recommended_jobs, action_plan } = data

  const totalSteps = action_plan?.length || 0
  const completedSteps = Object.values(checkedItems).filter(Boolean).length
  const progressPercentage = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0

  const primaryPath = career_paths?.[0]
  const matchFit = primaryPath?.match_level 
    ? primaryPath.match_level.replace('_', ' ').toUpperCase()
    : 'STRONG MATCH'

  const matchFitClass = primaryPath?.match_level || 'strong_match'

  return (
    <div className="career-results-page page-container">
      {/* Hero Header Banner */}
      <div className="career-results-hero">
        <div className="career-results-hero__content">
          <h1 className="career-results-hero__title">{target_role} Dashboard</h1>
          <div className="career-results-hero__meta">
            <div className="career-results-hero__meta-item">
              <span className="career-results-hero__meta-icon">📍</span>
              <span>Location: <strong>{location}</strong></span>
            </div>
            <div className="career-results-hero__meta-item">
              <span className="career-results-hero__meta-icon">📄</span>
              <span>Based on: <strong>{resume_filename ? `Resume (${resume_filename})` : 'Self-Input Profile'}</strong></span>
            </div>
          </div>
        </div>
        <Link to="/career-advisor" className="career-results-hero__back-btn">
          <span>←</span> Back to Career Hub
        </Link>
      </div>

      {/* KPI Stats Bar */}
      <div className="career-kpi-bar">
        <div className="kpi-card">
          <div className="kpi-card__icon-wrapper">
            🎯
          </div>
          <div className="kpi-card__info">
            <span className="kpi-card__value">
              <span className={`badge badge--${matchFitClass}`} style={{ fontSize: '0.85rem', padding: '0.35rem 0.85rem' }}>
                {matchFit}
              </span>
            </span>
            <span className="kpi-card__label">Overall Match Fit</span>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card__icon-wrapper kpi-card__icon-wrapper--green">
            ⚡
          </div>
          <div className="kpi-card__info">
            <span className="kpi-card__value">{progressPercentage}%</span>
            <span className="kpi-card__label">Action Plan ({completedSteps}/{totalSteps})</span>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card__icon-wrapper kpi-card__icon-wrapper--cyan">
            💼
          </div>
          <div className="kpi-card__info">
            <span className="kpi-card__value">{recommended_jobs?.length || 0}</span>
            <span className="kpi-card__label">Live Matches</span>
          </div>
        </div>
      </div>

      {/* Grid: 2-column layout */}
      <div className="career-dashboard-grid">
        {/* Left Column: Career Paths & Salary */}
        <div className="career-dashboard-left">
          
          {/* Section 1: Career Paths */}
          <div className="card results-card">
            <h2 className="section-title">Recommended Career Paths</h2>
            <p className="section-subtitle-hint">Explore the best career options matched for you.</p>
            <div className="paths-list">
              {career_paths.map((path, idx) => (
                <div key={idx} className="path-item">
                  <div className="path-item__header">
                    <h3 className="path-item__title">{path.name}</h3>
                    <span className={`badge badge--${path.match_level || 'strong_match'}`}>
                      {path.match_level ? path.match_level.replace('_', ' ') : 'Strong Match'}
                    </span>
                  </div>
                  <p className="path-item__desc">{path.description}</p>
                  
                  {path.required_skills && path.required_skills.length > 0 && (
                    <div className="path-item__skills">
                      <span className="path-item__skills-label">Skills Needed:</span>
                      <div className="chips-container">
                        {path.required_skills.map((skill, sIdx) => (
                          <span key={sIdx} className="chip">{skill}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Section 2: Salary Insights */}
          {salary_insights && (
            <div className="card results-card">
              <h2 className="section-title">Salary & Market Insights</h2>
              <p className="section-subtitle-hint">Salary ranges and high-value skills in the market.</p>
              
              <div className="salary-stats">
                <div className="salary-stat-box">
                  <span className="salary-stat-box__label">Current Est. Salary</span>
                  <span className="salary-stat-box__value">{salary_insights.current_estimated || 'N/A'}</span>
                </div>
                <div className="salary-stat-box salary-stat-box--highlight">
                  <span className="salary-stat-box__label">Target Role Range</span>
                  <span className="salary-stat-box__value">{salary_insights.target_role_range || 'N/A'}</span>
                </div>
              </div>

              {salary_insights.top_paying_skills && salary_insights.top_paying_skills.length > 0 && (
                <div className="salary-skills">
                  <span className="salary-skills__label">Top Paying Skills for Target Role</span>
                  <div className="chips-container mt-sm">
                    {salary_insights.top_paying_skills.map((skill, idx) => (
                      <span key={idx} className="chip chip--accent">{skill}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Jobs & Action Plan */}
        <div className="career-dashboard-right">
          
          {/* Section 3: Action Plan */}
          <div className="card results-card">
            <h2 className="section-title">Interactive Action Plan</h2>
            <p className="section-subtitle-hint">Track your steps towards upskilling.</p>
            
            {/* Dynamic Progress Bar */}
            <div className="action-progress">
              <div className="action-progress__header">
                <span className="action-progress__label">Completeness</span>
                <span className="action-progress__val">{progressPercentage}%</span>
              </div>
              <div className="action-progress__bar-bg">
                <div 
                  className="action-progress__bar-fill" 
                  style={{ width: `${progressPercentage}%` }}
                ></div>
              </div>
            </div>

            <div className="checklist">
              {action_plan.map((step, idx) => (
                <label key={idx} className={`checklist-item ${checkedItems[idx] ? 'checklist-item--checked' : ''}`}>
                  <input
                    type="checkbox"
                    className="checklist-item__checkbox"
                    checked={!!checkedItems[idx]}
                    onChange={() => handleToggleCheck(idx)}
                  />
                  <span className="checklist-item__text">{step}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Section 4: Recommended Jobs */}
          <div className="card results-card">
            <h2 className="section-title">Matching Live Listings</h2>
            <p className="section-subtitle-hint">Current openings that match your target role.</p>
            <div className="jobs-list">
              {recommended_jobs.map((job, idx) => {
                // Generate initials for logo placeholder
                const initials = job.company ? job.company.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : 'JB'
                return (
                  <div key={idx} className="job-item">
                    <div className="job-item__body">
                      <div className="job-item__logo">
                        {initials}
                      </div>
                      <div className="job-item__content">
                        <h3 className="job-item__title">{job.title}</h3>
                        <p className="job-item__company">{job.company}</p>
                        <p className="job-item__location">📍 {job.location}</p>
                      </div>
                      {job.match_score && (
                        <div className="job-match-circle" title={`${job.match_score}% match`}>
                          <span className="job-match-circle__val">{job.match_score}%</span>
                        </div>
                      )}
                    </div>
                    <a
                      href={job.apply_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn--secondary btn--sm btn--block mt-sm"
                    >
                      View Listing
                    </a>
                  </div>
                )
              })}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
