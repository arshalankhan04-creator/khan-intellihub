/**
 * Full-screen premium loading overlay.
 * Props:
 *   title (string) - Main loading header
 *   description (string) - Descriptive text under the spinner
 */
export function LoadingOverlay({ title = "Processing", description = "Please wait..." }) {
  return (
    <div className="loading-overlay">
      <div className="loading-overlay__container">
        <div className="loading-overlay__spinner" />
        <h2 className="loading-overlay__title">{title}</h2>
        <p className="loading-overlay__desc">{description}</p>
      </div>
    </div>
  )
}
