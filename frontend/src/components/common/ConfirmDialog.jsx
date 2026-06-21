/**
 * Modal confirmation dialog.
 * Reusable by any module — not tied to resume logic.
 *
 * Props:
 *   isOpen    boolean  — controls visibility
 *   message   string   — question to display to the user
 *   onConfirm fn       — called when user clicks Confirm
 *   onCancel  fn       — called when user clicks Cancel or presses Escape
 *   isLoading boolean  — disables Confirm and shows "Deleting..." while request is in flight
 */
import { useEffect } from 'react'

export function ConfirmDialog({ isOpen, message, onConfirm, onCancel, isLoading = false }) {
  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return
    function handleKey(e) {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [isOpen, onCancel])

  if (!isOpen) return null

  return (
    <div className="dialog-overlay" onClick={onCancel}>
      <div
        className="dialog"
        role="dialog"
        aria-modal="true"
        onClick={e => e.stopPropagation()}
      >
        <p className="dialog__message">{message}</p>
        <div className="dialog__actions">
          <button
            type="button"
            className="btn btn--danger"
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? 'Deleting…' : 'Delete'}
          </button>
          <button
            type="button"
            className="btn btn--secondary"
            onClick={onCancel}
            disabled={isLoading}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
