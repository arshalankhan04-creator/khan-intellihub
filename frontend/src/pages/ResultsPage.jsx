/**
 * Results page — fetches and displays the full analysis for one resume.
 */
import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getResults } from '../api/resumeService'
import { LoadingSpinner }   from '../components/common/LoadingSpinner'
import { ErrorMessage }     from '../components/common/ErrorMessage'
import { ScoreGauge }       from '../components/resume/ScoreGauge'
import { ScoreBreakdown }   from '../components/resume/ScoreBreakdown'
import { FeedbackSection }  from '../components/resume/FeedbackSection'

export function ResultsPage() {
  const { resumeId } = useParams()
  const [data, setData]       = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError]     = useState('')

  useEffect(() => {
    setIsLoading(true)
    getResults(resumeId)
      .then(res => setData(res))
      .catch(err => {
        const code = err.response?.data?.code
        const msg  = err.response?.data?.error
        if (err.response?.status === 404) {
          setError('Resume not found.')
        } else if (err.response?.status === 403) {
          setError('You do not have permission to view this resume.')
        } else if (code === 'PROCESSING_FAILED') {
          setError(msg || 'Processing failed for this resume.')
        } else if (!err.response) {
          setError('Network error. Please check your connection.')
        } else {
          setError('Something went wrong. Please try again.')
        }
      })
      .finally(() => setIsLoading(false))
  }, [resumeId])

  if (isLoading) return <LoadingSpinner fullPage />

  if (error) {
    return (
      <div className="page-container">
        <ErrorMessage message={error} />
        <Link to="/history" className="link back-link">← Back to History</Link>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="results-page page-container">
      {/* Hero Header Banner */}
      <div className="career-results-hero">
        <div className="career-results-hero__content">
          <h1 className="career-results-hero__title" style={{ fontSize: '1.85rem' }}>{data.original_filename}</h1>
          <div className="career-results-hero__meta">
            <div className="career-results-hero__meta-item">
              <span className="career-results-hero__meta-icon">📋</span>
              <span>ATS Analysis Report</span>
            </div>
            <div className="career-results-hero__meta-item">
              <span className="career-results-hero__meta-icon">🕒</span>
              <span>Analyzed on: <strong>{new Date(data.created_at).toLocaleDateString()}</strong></span>
            </div>
          </div>
        </div>
        <Link to="/history" className="career-results-hero__back-btn">
          <span>←</span> Back to History
        </Link>
      </div>

      {/* Score + Breakdown Grid */}
      <div className="results-page__top">
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', margin: 0 }}>
          <ScoreGauge score={data.ats_score} />
        </div>
        <div className="card" style={{ margin: 0 }}>
          <ScoreBreakdown scores={data.scores} />
        </div>
      </div>

      {/* Full feedback report */}
      <FeedbackSection feedbackReport={data.feedback_report} />
    </div>
  )
}
