/**
 * Inline error banner.
 * Props:
 *   message   string  — the error text to display
 *   onDismiss fn|null — if provided, shows an × button
 */
export function ErrorMessage({ message, onDismiss }) {
  if (!message) return null

  return (
    <div className="error-message" role="alert">
      <span>{message}</span>
      {onDismiss && (
        <button
          type="button"
          className="error-message__dismiss"
          onClick={onDismiss}
          aria-label="Dismiss error"
        >
          ×
        </button>
      )}
    </div>
  )
}
