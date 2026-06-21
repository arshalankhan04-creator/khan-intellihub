/**
 * Paginated resume history table.
 *
 * Props:
 *   records       array    — current page of resume records
 *   totalCount    number   — total records across all pages
 *   page          number   — current page number (1-based)
 *   pageSize      number   — records per page
 *   onPageChange  fn(n)    — called with new page number
 *   onDelete      fn(id)   — called when Delete is clicked for a record
 *   deletingId    string|null — resume_id currently being deleted (shows spinner)
 */
import { useNavigate } from 'react-router-dom'
import { formatDate, getStatusLabel, getStatusColor } from '../../utils/formatters'

export function HistoryTable({
  records,
  totalCount,
  page,
  pageSize,
  onPageChange,
  onDelete,
  deletingId,
}) {
  const navigate = useNavigate()
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize))

  if (!records || records.length === 0) {
    return (
      <div className="history-empty">
        <p>No resumes yet.</p>
        <button
          type="button"
          className="btn btn--primary"
          onClick={() => navigate('/upload')}
        >
          Upload your first resume
        </button>
      </div>
    )
  }

  return (
    <div className="history-table-wrapper">
      <table className="history-table">
        <thead>
          <tr>
            <th>Filename</th>
            <th>Uploaded</th>
            <th>Status</th>
            <th>ATS Score</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {records.map(record => (
            <tr key={record.resume_id}>
              <td className="history-table__filename" title={record.original_filename}>
                {record.original_filename}
              </td>
              <td>{formatDate(record.upload_timestamp)}</td>
              <td>
                <span className={`status-badge ${getStatusColor(record.status)}`}>
                  {getStatusLabel(record.status)}
                </span>
              </td>
              <td>
                {record.ats_score !== null && record.ats_score !== undefined
                  ? record.ats_score
                  : '—'}
              </td>
              <td className="history-table__actions">
                <button
                  type="button"
                  className="btn btn--sm btn--secondary"
                  onClick={() => navigate(`/results/${record.resume_id}`)}
                >
                  View
                </button>
                <button
                  type="button"
                  className="btn btn--sm btn--danger"
                  onClick={() => onDelete(record.resume_id)}
                  disabled={deletingId === record.resume_id}
                >
                  {deletingId === record.resume_id ? '…' : 'Delete'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Pagination */}
      <div className="pagination">
        <button
          type="button"
          className="btn btn--sm btn--secondary"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          ← Previous
        </button>
        <span className="pagination__info">
          Page {page} of {totalPages}
        </span>
        <button
          type="button"
          className="btn btn--sm btn--secondary"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
        >
          Next →
        </button>
      </div>
    </div>
  )
}
