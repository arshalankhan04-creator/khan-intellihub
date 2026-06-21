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
      <div className="results-page__header">
        <h1 className="page-title">{data.original_filename}</h1>
        <Link to="/history" className="link back-link">← Back to History</Link>
      </div>

      {/* Score + Breakdown side by side on larger screens */}
      <div className="results-page__top">
        <ScoreGauge score={data.ats_score} />
        <ScoreBreakdown scores={data.scores} />
      </div>

      {/* Full feedback report */}
      <FeedbackSection feedbackReport={data.feedback_report} />
    </div>
  )
}
