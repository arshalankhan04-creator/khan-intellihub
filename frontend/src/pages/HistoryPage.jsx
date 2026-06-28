/**
 * Unified History page — paginated lists for both Resumes and Career Advice
 * with segmented control tabs and deletion dialogs.
 */
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listResumes, deleteResume } from '../api/resumeService'
import { getAdviceHistory, deleteAdviceRecord } from '../api/careerAdvisorService'
import { LoadingSpinner }  from '../components/common/LoadingSpinner'
import { ErrorMessage }    from '../components/common/ErrorMessage'
import { ConfirmDialog }   from '../components/common/ConfirmDialog'
import { HistoryTable }    from '../components/resume/HistoryTable'

const PAGE_SIZE = 10

export function HistoryPage() {
  const [activeTab, setActiveTab] = useState('resumes') // 'resumes' or 'advice'

  // Resumes states
  const [resumePage, setResumePage]       = useState(1)
  const [resumes, setResumes]             = useState([])
  const [resumeTotal, setResumeTotal]     = useState(0)
  const [resumeLoading, setResumeLoading] = useState(true)

  // Advice states
  const [advicePage, setAdvicePage]       = useState(1)
  const [adviceRecords, setAdviceRecords] = useState([])
  const [adviceTotal, setAdviceTotal]     = useState(0)
  const [adviceLoading, setAdviceLoading] = useState(true)

  const [fetchError, setFetchError] = useState('')
  const [deleteError, setDeleteError] = useState('')

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null) // { id: string, type: 'resume' | 'advice' }
  const [deletingId, setDeletingId] = useState(null)

  // Fetch Resumes
  useEffect(() => {
    let cancelled = false
    setResumeLoading(true)
    setFetchError('')

    listResumes({ page: resumePage, page_size: PAGE_SIZE })
      .then(data => {
        if (cancelled) return
        setResumes(data.results)
        setResumeTotal(data.total_count)
      })
      .catch(() => {
        if (!cancelled) setFetchError('Could not load your resumes. Please refresh.')
      })
      .finally(() => {
        if (!cancelled) setResumeLoading(false)
      })

    return () => { cancelled = true }
  }, [resumePage])

  // Fetch Advice
  useEffect(() => {
    let cancelled = false
    setAdviceLoading(true)
    setFetchError('')

    getAdviceHistory({ page: advicePage, page_size: PAGE_SIZE })
      .then(data => {
        if (cancelled) return
        setAdviceRecords(data.results)
        setAdviceTotal(data.total_count)
      })
      .catch(() => {
        if (!cancelled) setFetchError('Could not load your career advice history. Please refresh.')
      })
      .finally(() => {
        if (!cancelled) setAdviceLoading(false)
      })

    return () => { cancelled = true }
  }, [advicePage])

  // Delete handlers
  function handleDeleteClick(id, type) {
    setDeleteTarget({ id, type })
    setDialogOpen(true)
  }

  function handleCancelDelete() {
    setDialogOpen(false)
    setDeleteTarget(null)
  }

  async function handleConfirmDelete() {
    if (!deleteTarget) return
    const { id, type } = deleteTarget
    setDeletingId(id)
    setDeleteError('')

    try {
      if (type === 'resume') {
        await deleteResume(id)
        setResumes(prev => prev.filter(r => r.resume_id !== id))
        setResumeTotal(prev => prev - 1)
      } else {
        await deleteAdviceRecord(id)
        setAdviceRecords(prev => prev.filter(r => r.id !== id))
        setAdviceTotal(prev => prev - 1)
      }
      setDialogOpen(false)
      setDeleteTarget(null)
    } catch {
      setDeleteError(`Failed to delete the ${type === 'resume' ? 'resume' : 'career advice record'}. Please try again.`)
      setDialogOpen(false)
    } finally {
      setDeletingId(null)
    }
  }

  const adviceTotalPages = Math.ceil(adviceTotal / PAGE_SIZE)

  return (
    <div className="page-container">
      <h1 className="page-title">System History</h1>
      <p className="page-subtitle">Manage all your resume analyses and AI career recommendations.</p>

      <ErrorMessage message={fetchError}  onDismiss={() => setFetchError('')} />
      <ErrorMessage message={deleteError} onDismiss={() => setDeleteError('')} />

      {/* Segmented Control Tabs */}
      <div className="tab-header" style={{ maxWidth: '440px', margin: '0 auto 2rem auto' }}>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'resumes' ? 'tab-btn--active' : ''}`}
          onClick={() => setActiveTab('resumes')}
        >
          Resume Analyses
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'advice' ? 'tab-btn--active' : ''}`}
          onClick={() => setActiveTab('advice')}
        >
          Career Recommendations
        </button>
      </div>

      {activeTab === 'resumes' ? (
        resumeLoading ? (
          <LoadingSpinner />
        ) : resumes.length === 0 ? (
          <div className="empty-state card" style={{ textAlign: 'center', padding: '3rem' }}>
            <p style={{ color: 'var(--color-muted)', fontSize: '1.05rem' }}>No resumes uploaded yet.</p>
            <Link to="/upload" className="btn btn--primary mt-sm" style={{ display: 'inline-block' }}>
              Upload Your First Resume
            </Link>
          </div>
        ) : (
          <HistoryTable
            records={resumes}
            totalCount={resumeTotal}
            page={resumePage}
            pageSize={PAGE_SIZE}
            onPageChange={setResumePage}
            onDelete={(id) => handleDeleteClick(id, 'resume')}
            deletingId={deletingId}
          />
        )
      ) : (
        adviceLoading ? (
          <LoadingSpinner />
        ) : adviceRecords.length === 0 ? (
          <div className="empty-state card" style={{ textAlign: 'center', padding: '3rem' }}>
            <p style={{ color: 'var(--color-muted)', fontSize: '1.05rem' }}>No career advice records generated yet.</p>
            <Link to="/career-advisor" className="btn btn--primary mt-sm" style={{ display: 'inline-block' }}>
              Create Custom Career Plan
            </Link>
          </div>
        ) : (
          <div className="advice-history-section">
            <div className="history-list" style={{ display: 'grid', gap: '1.25rem', marginBottom: '2rem' }}>
              {adviceRecords.map(record => (
                <div key={record.id} className="card history-item" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 0 }}>
                  <div className="history-item__info">
                    <h3 className="history-item__title" style={{ fontSize: '1.15rem', marginBottom: '0.25rem' }}>{record.target_role}</h3>
                    <p className="history-item__meta" style={{ color: 'var(--color-muted)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
                      📍 {record.location} | 📄 {record.resume_filename ? `Resume: ${record.resume_filename}` : 'Self-Input Profile'}
                    </p>
                    <span className="history-item__date" style={{ fontSize: '0.8rem', color: 'var(--color-muted)' }}>
                      Created: {new Date(record.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="history-item__actions" style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
                    <Link to={`/career-advisor/${record.id}`} className="btn btn--secondary btn--sm">
                      View Dashboard
                    </Link>
                    <button
                      type="button"
                      className="btn btn--danger btn--sm"
                      onClick={() => handleDeleteClick(record.id, 'advice')}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {adviceTotalPages > 1 && (
              <div className="pagination" style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1.5rem' }}>
                <button
                  type="button"
                  className="btn btn--secondary btn--sm"
                  disabled={advicePage === 1}
                  onClick={() => setAdvicePage(prev => prev - 1)}
                >
                  Previous
                </button>
                <span style={{ display: 'flex', alignItems: 'center', fontSize: '0.9rem', color: 'var(--color-muted)', padding: '0 0.5rem' }}>
                  Page {advicePage} of {adviceTotalPages}
                </span>
                <button
                  type="button"
                  className="btn btn--secondary btn--sm"
                  disabled={advicePage === adviceTotalPages}
                  onClick={() => setAdvicePage(prev => prev + 1)}
                >
                  Next
                </button>
              </div>
            )}
          </div>
        )
      )}

      <ConfirmDialog
        isOpen={dialogOpen}
        message={`Are you sure you want to delete this ${deleteTarget?.type === 'resume' ? 'resume analysis' : 'career advisor roadmap'}? This cannot be undone.`}
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        isLoading={!!deletingId}
      />
    </div>
  )
}
