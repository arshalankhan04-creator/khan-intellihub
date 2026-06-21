/**
 * Upload page — renders UploadForm and navigates to results on success.
 */
import { useNavigate } from 'react-router-dom'
import { UploadForm } from '../components/resume/UploadForm'

export function UploadPage() {
  const navigate = useNavigate()

  return (
    <div className="page-container">
      <h1 className="page-title">Analyze Your Resume</h1>
      <p className="page-subtitle">
        Upload a PDF to receive your ATS score and personalized feedback.
      </p>
      <UploadForm onSuccess={resumeId => navigate(`/results/${resumeId}`)} />
    </div>
  )
}
