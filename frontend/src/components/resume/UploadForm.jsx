/**
 * Resume upload form with drag-and-drop support.
 * Props:
 *   onSuccess(resumeId)  called after a successful upload
 */
import { useState, useRef } from 'react'
import { uploadResume } from '../../api/resumeService'
import { ErrorMessage } from '../common/ErrorMessage'
import { LoadingOverlay } from '../common/LoadingOverlay'

export function UploadForm({ onSuccess }) {
  const [selectedFile, setSelectedFile]   = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [isLoading, setIsLoading]         = useState(false)
  const [error, setError]                 = useState('')
  const [isDragging, setIsDragging]       = useState(false)
  const fileInputRef = useRef(null)

  function handleFileChange(file) {
    if (!file) return
    setSelectedFile(file)
    setError('')
  }

  function handleInputChange(e) {
    handleFileChange(e.target.files[0])
  }

  function handleDragOver(e) {
    e.preventDefault()
    setIsDragging(true)
  }

  function handleDragLeave() {
    setIsDragging(false)
  }

  function handleDrop(e) {
    e.preventDefault()
    setIsDragging(false)
    handleFileChange(e.dataTransfer.files[0])
  }

  function handleRemove() {
    setSelectedFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!selectedFile) return

    setIsLoading(true)
    setError('')

    try {
      const data = await uploadResume(selectedFile, jobDescription)
      onSuccess(data.resume_id)
    } catch (err) {
      const code    = err.response?.data?.code
      const message = err.response?.data?.error

      if (code === 'FILE_TOO_LARGE') {
        setError('File size must not exceed 5 MB.')
      } else if (code === 'UNSUPPORTED_MEDIA_TYPE') {
        setError('Only PDF files are accepted.')
      } else if (code === 'PROCESSING_FAILED') {
        setError(message || 'Processing failed. Please try again.')
      } else if (!err.response) {
        setError('Network error. Please check your connection.')
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      {isLoading && (
        <LoadingOverlay 
          title="Analyzing Resume" 
          description="Khan IntelliHub is parsing, scoring, and generating feedback for your resume. This may take a few seconds..." 
        />
      )}
      <ErrorMessage message={error} onDismiss={() => setError('')} />

      {/* Drop zone */}
      <div
        className={`drop-zone ${isDragging ? 'drop-zone--active' : ''} ${selectedFile ? 'drop-zone--has-file' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !selectedFile && fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload area"
        onKeyDown={e => e.key === 'Enter' && !selectedFile && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          style={{ display: 'none' }}
          onChange={handleInputChange}
        />

        {selectedFile ? (
          <div className="drop-zone__selected">
            <span className="drop-zone__filename">📄 {selectedFile.name}</span>
            <button
              type="button"
              className="drop-zone__remove"
              onClick={e => { e.stopPropagation(); handleRemove() }}
            >
              Remove
            </button>
          </div>
        ) : (
          <div className="drop-zone__empty">
            <span className="drop-zone__icon">📤</span>
            <p className="drop-zone__primary">Drop your PDF here</p>
            <p className="drop-zone__secondary">or click to browse</p>
            <p className="drop-zone__hint">PDF only · Max 5 MB</p>
          </div>
        )}
      </div>

      {/* Optional Job Description */}
      <div className="form-group">
        <label htmlFor="jd" className="form-label">
          Job Description <span className="form-label--optional">(optional)</span>
        </label>
        <textarea
          id="jd"
          className="form-textarea"
          rows={5}
          maxLength={10000}
          value={jobDescription}
          onChange={e => setJobDescription(e.target.value)}
          placeholder="Paste the job description here to tailor your ATS score…"
          disabled={isLoading}
        />
      </div>

      <button
        type="submit"
        className="btn btn--primary btn--full"
        disabled={!selectedFile || isLoading}
      >
        {isLoading ? 'Analyzing…' : 'Analyze Resume'}
      </button>
    </form>
  )
}
