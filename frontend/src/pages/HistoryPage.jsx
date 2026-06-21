/**
 * History page — paginated resume list with inline delete confirmation.
 */
import { useState, useEffect } from 'react'
import { listResumes, deleteResume } from '../api/resumeService'
import { LoadingSpinner }  from '../components/common/LoadingSpinner'
import { ErrorMessage }    from '../components/common/ErrorMessage'
import { ConfirmDialog }   from '../components/common/ConfirmDialog'
import { HistoryTable }    from '../components/resume/HistoryTable'

const PAGE_SIZE = 10

export function HistoryPage() {
  const [page, setPage]             = useState(1)
  const [records, setRecords]       = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [isLoading, setIsLoading]   = useState(true)
  const [fetchError, setFetchError] = useState('')
  const [deleteError, setDeleteError] = useState('')

  // Dialog state
  const [dialogOpen, setDialogOpen]           = useState(false)
  const [selectedResumeId, setSelectedResumeId] = useState(null)
  const [deletingId, setDeletingId]           = useState(null)

  // Fetch the current page
  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setFetchError('')

    listResumes({ page, page_size: PAGE_SIZE })
      .then(data => {
        if (cancelled) return
        setRecords(data.results)
        setTotalCount(data.total_count)
      })
      .catch(() => {
        if (!cancelled) setFetchError('Could not load your resumes. Please refresh.')
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => { cancelled = true }
  }, [page])

  // ── Delete flow ─────────────────────────────────────────────────────────

  function handleDeleteClick(resumeId) {
    setSelectedResumeId(resumeId)
    setDialogOpen(true)
  }

  function handleCancelDelete() {
    setDialogOpen(false)
    setSelectedResumeId(null)
  }

  async function handleConfirmDelete() {
    if (!selectedResumeId) return
    setDeletingId(selectedResumeId)
    setDeleteError('')

    try {
      await deleteResume(selectedResumeId)

      // Remove from local state without re-fetching
      setRecords(prev => prev.filter(r => r.resume_id !== selectedResumeId))
      setTotalCount(prev => prev - 1)

      setDialogOpen(false)
      setSelectedResumeId(null)
    } catch {
      setDeleteError('Failed to delete the resume. Please try again.')
      setDialogOpen(false)
    } finally {
      setDeletingId(null)
    }
  }

  // ────────────────────────────────────────────────────────────────────────

  if (isLoading) return <LoadingSpinner fullPage />

  return (
    <div className="page-container">
      <h1 className="page-title">Resume History</h1>

      <ErrorMessage message={fetchError}  onDismiss={() => setFetchError('')} />
      <ErrorMessage message={deleteError} onDismiss={() => setDeleteError('')} />

      <HistoryTable
        records={records}
        totalCount={totalCount}
        page={page}
        pageSize={PAGE_SIZE}
        onPageChange={setPage}
        onDelete={handleDeleteClick}
        deletingId={deletingId}
      />

      <ConfirmDialog
        isOpen={dialogOpen}
        message="Are you sure you want to delete this resume? This cannot be undone."
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        isLoading={!!deletingId}
      />
    </div>
  )
}
