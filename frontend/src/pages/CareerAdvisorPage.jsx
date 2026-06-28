import { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { listResumes, uploadResume } from '../api/resumeService'
import { generateAdvice, getAdviceHistory, deleteAdviceRecord } from '../api/careerAdvisorService'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorMessage } from '../components/common/ErrorMessage'
import { LoadingOverlay } from '../components/common/LoadingOverlay'

export function CareerAdvisorPage() {
  const navigate = useNavigate()
  
  // Tabs: 'resume' or 'manual'
  const [activeTab, setActiveTab] = useState('resume')
  
  // Resume option: 'upload' or 'select'
  const [resumeOption, setResumeOption] = useState('upload')
  const [uploadFile, setUploadFile] = useState(null)
  
  // Resumes list for Tab 1
  const [resumes, setResumes] = useState([])
  const [loadingResumes, setLoadingResumes] = useState(false)
  
  // History list
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  
  // Form values
  const [selectedResumeId, setSelectedResumeId] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [location, setLocation] = useState('')
  const [manualSkills, setManualSkills] = useState('')
  
  // Loading & Error states
  const [generating, setGenerating] = useState(false)
  const [formError, setFormError] = useState('')
  


  // Searchable dropdown states and refs
  const [jobDropdownOpen, setJobDropdownOpen] = useState(false)
  const [locDropdownOpen, setLocDropdownOpen] = useState(false)

  const jobRef = useRef(null)
  const locRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(event) {
      if (jobRef.current && !jobRef.current.contains(event.target)) {
        setJobDropdownOpen(false)
      }
      if (locRef.current && !locRef.current.contains(event.target)) {
        setLocDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const jobSuggestions = [
    'Software Engineer', 'Full-Stack Developer', 'Frontend Developer', 'Backend Developer',
    'DevOps Engineer', 'Data Analyst', 'Data Scientist', 'Machine Learning Engineer',
    'Civil Engineer', 'Mechanical Engineer', 'Financial Analyst', 'Finance Manager',
    'Marketing Coordinator', 'Digital Marketing Specialist', 'Digital Marketing Manager',
    'Healthcare Administrator', 'Healthcare Manager', 'Product Manager', 'Project Manager',
    'QA Engineer', 'React Developer', 'Python Developer', 'Java Developer'
  ]

  const locationSuggestions = [
    'Remote', 'San Francisco, CA', 'New York, NY', 'Seattle, WA', 'Austin, TX',
    'Los Angeles, CA', 'Boston, MA', 'Chicago, IL', 'Denver, CO', 'Atlanta, GA',
    'London, UK', 'Toronto, ON', 'Bangalore, India', 'Berlin, Germany',
    'Paris, France', 'Sydney, Australia'
  ]

  const filteredJobs = targetRole.trim() === ''
    ? jobSuggestions
    : jobSuggestions.filter(item => item.toLowerCase().includes(targetRole.toLowerCase()))

  const filteredLocs = location.trim() === ''
    ? locationSuggestions
    : locationSuggestions.filter(item => item.toLowerCase().includes(location.toLowerCase()))

  async function handleDelete(recordId) {
    if (!window.confirm("Are you sure you want to delete this career advice record?")) {
      return
    }
    try {
      await deleteAdviceRecord(recordId)
      setHistory(prev => prev.filter(item => item.id !== recordId))
    } catch (err) {
      console.error("Failed to delete record", err)
      alert("Failed to delete the record. Please try again.")
    }
  }

  useEffect(() => {
    // Fetch completed resumes for dropdown
    setLoadingResumes(true)
    listResumes({ page: 1, page_size: 50 })
      .then(data => {
        // Only keep COMPLETED resumes
        const completed = data.results.filter(r => r.status === 'COMPLETED')
        setResumes(completed)
        if (completed.length > 0) {
          setSelectedResumeId(completed[0].resume_id)
        }
      })
      .catch(err => console.error("Failed to load resumes", err))
      .finally(() => setLoadingResumes(false))
  }, [])

  useEffect(() => {
    // Fetch recent 3 advice history items
    setLoadingHistory(true)
    getAdviceHistory({ page: 1, page_size: 3 })
      .then(data => {
        setHistory(data.results)
      })
      .catch(err => console.error("Failed to load history", err))
      .finally(() => setLoadingHistory(false))
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setFormError('')
    setGenerating(true)

    try {
      let adviceRecord
      if (activeTab === 'resume') {
        let resumeId = selectedResumeId
        
        if (resumeOption === 'upload') {
          if (!uploadFile) {
            throw new Error('Please select a PDF file to upload.')
          }
          // Step 1: Upload and analyze
          const uploadResult = await uploadResume(uploadFile, null)
          resumeId = uploadResult.resume_id
        }

        if (!resumeId) {
          throw new Error('Please select an analyzed resume or upload one.')
        }
        
        // Step 2: Generate advice
        adviceRecord = await generateAdvice(resumeId, targetRole, location)
      } else {
        // Manual mode
        const skillsArray = manualSkills
          .split(',')
          .map(s => s.trim())
          .filter(s => s.length > 0)
        
        if (skillsArray.length === 0) {
          throw new Error('Please enter at least one skill.')
        }
        adviceRecord = await generateAdvice(null, targetRole, location, skillsArray)
      }
      
      // Navigate to results
      navigate(`/career-advisor/${adviceRecord.id}`)
    } catch (err) {
      setFormError(err.response?.data?.error || err.message || 'Failed to generate career advice.')
      setGenerating(false)
    }
  }

  return (
    <div className="career-advisor-page page-container">
      {generating && (
        <LoadingOverlay
          title={resumeOption === 'upload' && activeTab === 'resume' ? "Uploading & Analyzing Resume" : "Generating Career Roadmap"}
          description={
            resumeOption === 'upload' && activeTab === 'resume'
              ? "Khan IntelliHub is parsing, scoring, and analyzing your resume first..."
              : "Generating custom career paths, salary metrics, action plan checklist, and matching live job listings..."
          }
        />
      )}
      <div className="career-advisor-page__header">
        <h1 className="page-title">AI Career Advisor</h1>
        <p className="page-subtitle">Get custom career paths, salary insights, checklists, and matching job listings.</p>
      </div>

      <div className="career-advisor-layout">
        {/* Left column: Generator Form */}
        <div className="card career-advisor-card">
          <div className="tab-header">
            <button
              type="button"
              className={`tab-btn ${activeTab === 'resume' ? 'tab-btn--active' : ''}`}
              onClick={() => setActiveTab('resume')}
              disabled={generating}
            >
              Analyze with Resume
            </button>
            <button
              type="button"
              className={`tab-btn ${activeTab === 'manual' ? 'tab-btn--active' : ''}`}
              onClick={() => setActiveTab('manual')}
              disabled={generating}
            >
              Manual Profile Setup
            </button>
          </div>

          <form onSubmit={handleSubmit} className="form career-form">
            {formError && <ErrorMessage message={formError} />}

            {activeTab === 'resume' ? (
              <div className="form-group">
                <label className="form-label" style={{ marginBottom: '0.5rem' }}>Resume Source</label>
                <div className="radio-group" style={{ display: 'flex', flexWrap: 'wrap', gap: '1.5rem', marginBottom: '1.25rem' }}>
                  <label className="radio-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem' }}>
                    <input
                      type="radio"
                      name="resumeOption"
                      value="upload"
                      checked={resumeOption === 'upload'}
                      onChange={() => setResumeOption('upload')}
                      disabled={generating}
                    />
                    Upload and Analyze a Resume
                  </label>
                  <label className="radio-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem' }}>
                    <input
                      type="radio"
                      name="resumeOption"
                      value="select"
                      checked={resumeOption === 'select'}
                      onChange={() => setResumeOption('select')}
                      disabled={generating}
                    />
                    Select from Previously Uploaded Resumes
                  </label>
                </div>

                {resumeOption === 'upload' ? (
                  <div className="form-group">
                    <label className="form-label" htmlFor="resumeFile">Upload PDF Resume</label>
                    <input
                      id="resumeFile"
                      type="file"
                      accept=".pdf"
                      className="form-input"
                      onChange={(e) => setUploadFile(e.target.files[0])}
                      disabled={generating}
                      required
                    />
                  </div>
                ) : (
                  <div className="form-group">
                    <label className="form-label" htmlFor="resumeSelect">Select Analyzed Resume</label>
                    {loadingResumes ? (
                      <div className="loading-small">Loading resumes...</div>
                    ) : resumes.length === 0 ? (
                      <div className="form-helper-error">
                        No completed resumes found. Please upload a new resume or select manual profile setup.
                      </div>
                    ) : (
                      <select
                        id="resumeSelect"
                        className="form-input"
                        value={selectedResumeId}
                        onChange={(e) => setSelectedResumeId(e.target.value)}
                        disabled={generating}
                      >
                        {resumes.map(r => (
                          <option key={r.resume_id} value={r.resume_id}>
                            {r.original_filename} (ATS: {r.ats_score})
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="form-group">
                <label className="form-label" htmlFor="manualSkills">My Professional Skills</label>
                <textarea
                  id="manualSkills"
                  className="form-input"
                  rows="3"
                  placeholder="e.g. Python, SQL, Git, React, Project Management (comma-separated)"
                  value={manualSkills}
                  onChange={(e) => setManualSkills(e.target.value)}
                  disabled={generating}
                  required
                />
                <span className="form-helper">Enter your skills separated by commas.</span>
              </div>
            )}

            <div className="form-row">
              <div className="form-group autocomplete-container" ref={jobRef}>
                <label className="form-label" htmlFor="targetRole">Target Job Title</label>
                <div className="searchable-dropdown">
                  <input
                    id="targetRole"
                    type="text"
                    className="form-input searchable-dropdown__input"
                    value={targetRole}
                    onChange={(e) => {
                      setTargetRole(e.target.value)
                      setJobDropdownOpen(true)
                    }}
                    onClick={() => setJobDropdownOpen(true)}
                    placeholder="Select or search job title..."
                    disabled={generating}
                    required
                    autoComplete="off"
                  />
                  <button
                    type="button"
                    className={`searchable-dropdown__chevron ${jobDropdownOpen ? 'searchable-dropdown__chevron--open' : ''}`}
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      setJobDropdownOpen(!jobDropdownOpen)
                    }}
                    disabled={generating}
                  >
                    ▼
                  </button>
                </div>
                {jobDropdownOpen && (
                  <ul className="suggestions-list">
                    {filteredJobs.length > 0 ? (
                      filteredJobs.map((item, idx) => (
                        <li
                          key={idx}
                          className="suggestion-item"
                          onClick={() => {
                            setTargetRole(item)
                            setJobDropdownOpen(false)
                          }}
                        >
                          {item}
                        </li>
                      ))
                    ) : (
                      <li className="suggestion-item suggestion-item--no-results">No matches found</li>
                    )}
                  </ul>
                )}
              </div>

              <div className="form-group autocomplete-container" ref={locRef}>
                <label className="form-label" htmlFor="location">Target Location</label>
                <div className="searchable-dropdown">
                  <input
                    id="location"
                    type="text"
                    className="form-input searchable-dropdown__input"
                    value={location}
                    onChange={(e) => {
                      setLocation(e.target.value)
                      setLocDropdownOpen(true)
                    }}
                    onClick={() => setLocDropdownOpen(true)}
                    placeholder="Select or search location..."
                    disabled={generating}
                    required
                    autoComplete="off"
                  />
                  <button
                    type="button"
                    className={`searchable-dropdown__chevron ${locDropdownOpen ? 'searchable-dropdown__chevron--open' : ''}`}
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      setLocDropdownOpen(!locDropdownOpen)
                    }}
                    disabled={generating}
                  >
                    ▼
                  </button>
                </div>
                {locDropdownOpen && (
                  <ul className="suggestions-list">
                    {filteredLocs.length > 0 ? (
                      filteredLocs.map((item, idx) => (
                        <li
                          key={idx}
                          className="suggestion-item"
                          onClick={() => {
                            setLocation(item)
                            setLocDropdownOpen(false)
                          }}
                        >
                          {item}
                        </li>
                      ))
                    ) : (
                      <li className="suggestion-item suggestion-item--no-results">No matches found</li>
                    )}
                  </ul>
                )}
              </div>
            </div>

            <button
              type="submit"
              className="btn btn--primary btn--block"
              disabled={generating || (activeTab === 'resume' && resumeOption === 'select' && resumes.length === 0)}
            >
              {generating 
                ? (resumeOption === 'upload' && activeTab === 'resume' ? 'Uploading & Analyzing Resume...' : 'Generating Advice...') 
                : 'Generate Career Plan'}
            </button>
          </form>
        </div>

        {/* Right column / bottom row: Advice History */}
        <div className="card history-card career-history-card">
          <h2 className="section-title">Recent Advice History</h2>
          {loadingHistory ? (
            <LoadingSpinner />
          ) : history.length === 0 ? (
            <div className="empty-state">
              <p>No career advice records generated yet.</p>
            </div>
          ) : (
            <div className="history-list">
              {history.map(record => (
                <div key={record.id} className="history-item">
                  <div className="history-item__info">
                    <h3 className="history-item__title">{record.target_role}</h3>
                    <p className="history-item__meta">
                      {record.location} | {record.resume_filename ? `Resume: ${record.resume_filename}` : 'Self-Input Profile'}
                    </p>
                    <span className="history-item__date">
                      {new Date(record.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="history-item__actions" style={{ display: 'flex', gap: '0.5rem' }}>
                    <Link to={`/career-advisor/${record.id}`} className="btn btn--secondary btn--sm">
                      View Dashboard
                    </Link>
                    <button
                      type="button"
                      className="btn btn--danger btn--sm"
                      onClick={() => handleDelete(record.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
