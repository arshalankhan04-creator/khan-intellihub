/**
 * Reusable loading spinner.
 * fullPage=true  → centred on screen, blocks content
 * fullPage=false → inline, sized to fit context
 */
export function LoadingSpinner({ fullPage = false }) {
  if (fullPage) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '60vh',
      }}>
        <div className="spinner" aria-label="Loading" />
      </div>
    )
  }

  return <span className="spinner spinner--inline" aria-label="Loading" />
}
