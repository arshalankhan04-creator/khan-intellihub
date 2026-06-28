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

  return (
    <div className="career-results-page page-container">
      {/* Header */}
      <div className="career-results-page__header">
        <div>
          <h1 className="page-title">{target_role} Dashboard</h1>
          <p className="page-subtitle">
            Location: <strong>{location}</strong> | Based on: <strong>{resume_filename ? `Resume (${resume_filename})` : 'Self-Input Profile'}</strong>
          </p>
        </div>
        <Link to="/career-advisor" className="link back-link">← Back to Career Hub</Link>
      </div>

      {/* Grid: 2-column layout */}
      <div className="career-dashboard-grid">
        {/* Left Column: Career Paths & Salary */}
        <div className="career-dashboard-left">
          
          {/* Section 1: Career Paths */}
          <div className="card results-card">
            <h2 className="section-title">Recommended Career Paths</h2>
            <div className="paths-grid">
              {career_paths.map((path, idx) => (
                <div key={idx} className="path-card">
                  <div className="path-card__header">
                    <h3 className="path-card__title">{path.name}</h3>
                    <span className={`badge badge--${path.match_level || 'strong_match'}`}>
                      {path.match_level ? path.match_level.replace('_', ' ') : 'Strong Match'}
                    </span>
                  </div>
                  <p className="path-card__desc">{path.description}</p>
                  
                  {path.required_skills && path.required_skills.length > 0 && (
                    <div className="path-card__skills">
                      <strong>Skills Needed:</strong>
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
              <div className="salary-grid">
                <div className="salary-card">
                  <span className="salary-card__label">Current Est. Salary</span>
                  <span className="salary-card__value">{salary_insights.current_estimated || 'N/A'}</span>
                </div>
                <div className="salary-card salary-card--highlight">
                  <span className="salary-card__label">Target Role Range</span>
                  <span className="salary-card__value">{salary_insights.target_role_range || 'N/A'}</span>
                </div>
                <div className="salary-card">
                  <span className="salary-card__label">Top Paying Skills</span>
                  <div className="chips-container mt-sm">
                    {salary_insights.top_paying_skills?.map((skill, idx) => (
                      <span key={idx} className="chip chip--accent">{skill}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Jobs & Action Plan */}
        <div className="career-dashboard-right">
          
          {/* Section 3: Recommended Jobs */}
          <div className="card results-card">
            <h2 className="section-title">Matching Live Listings</h2>
            <div className="jobs-list">
              {recommended_jobs.map((job, idx) => (
                <div key={idx} className="job-match-card">
                  <div className="job-match-card__header">
                    <div>
                      <h3 className="job-match-card__title">{job.title}</h3>
                      <p className="job-match-card__company">{job.company} — <small>{job.location}</small></p>
                    </div>
                    {job.match_score && (
                      <div className="job-match-score">
                        <span className="job-match-score__val">{job.match_score}%</span>
                        <span className="job-match-score__label">Match</span>
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
              ))}
            </div>
          </div>

          {/* Section 4: Action Plan */}
          <div className="card results-card">
            <h2 className="section-title">Interactive Action Plan</h2>
            <p className="section-subtitle">Track your steps towards transitioning or upskilling for the role.</p>
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

        </div>
      </div>
    </div>
  )
}
