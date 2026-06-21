/**
 * Utility helpers for formatting values in the UI.
 * Used by HistoryTable, ScoreGauge, and status badges.
 */

/**
 * Format an ISO timestamp into a readable date string.
 * e.g. "2025-06-15T10:30:00Z" → "15 Jun 2025"
 */
export function formatDate(isoString) {
  if (!isoString) return '—'
  const date = new Date(isoString)
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

/**
 * Map a backend status string to a human-readable label.
 */
export function getStatusLabel(status) {
  const labels = {
    PENDING: 'Pending',
    PARSED: 'Parsed',
    SCORED: 'Scored',
    COMPLETED: 'Completed',
    PARSE_FAILED: 'Parse Failed',
    SCORE_FAILED: 'Score Failed',
    FEEDBACK_FAILED: 'Feedback Failed',
  }
  return labels[status] || status
}

/**
 * Map a backend status string to a CSS class name for the badge.
 * Classes: status-green, status-yellow, status-red
 */
export function getStatusColor(status) {
  if (status === 'COMPLETED') return 'status-green'
  if (['PENDING', 'PARSED', 'SCORED'].includes(status)) return 'status-yellow'
  return 'status-red'
}

/**
 * Map a numeric ATS score (0–100) to a CSS colour class.
 * Classes: score-red, score-orange, score-yellow, score-green
 */
export function getScoreColor(score) {
  if (score === null || score === undefined) return 'score-grey'
  if (score >= 80) return 'score-green'
  if (score >= 60) return 'score-yellow'
  if (score >= 40) return 'score-orange'
  return 'score-red'
}

/**
 * Map a numeric score to a hex colour value (for SVG arc stroke).
 */
export function getScoreHex(score) {
  if (score === null || score === undefined) return '#9ca3af'
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#eab308'
  if (score >= 40) return '#f97316'
  return '#ef4444'
}
