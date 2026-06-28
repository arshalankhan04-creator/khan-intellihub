/**
 * Circular SVG arc gauge displaying the ATS score 0–100.
 * Colour-coded by tier: red / orange / yellow / green.
 */
import { getScoreHex } from '../../utils/formatters'

export function ScoreGauge({ score }) {
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const pct = score !== null && score !== undefined ? Math.min(100, Math.max(0, score)) : 0
  const offset = circumference - (pct / 100) * circumference
  const colour = getScoreHex(score)

  // Determine the score fit tier
  function getScoreTier(s) {
    if (s >= 80) return { label: 'Excellent Fit', class: 'badge--strong_match' }
    if (s >= 65) return { label: 'Good Fit', class: 'badge--partial_match' }
    if (s >= 40) return { label: 'Needs Optimization', class: 'badge--low_match' }
    return { label: 'Poor Fit', class: 'badge--low_match' }
  }

  const tier = getScoreTier(pct)

  return (
    <div className="score-gauge-wrapper" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <div className="score-gauge">
        <svg width="140" height="140" viewBox="0 0 140 140" aria-hidden="true" style={{ filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.05))' }}>
          {/* Background track */}
          <circle
            cx="70" cy="70" r={radius}
            fill="none"
            stroke="var(--color-surface-hover)"
            strokeWidth="11"
          />
          {/* Score arc */}
          <circle
            cx="70" cy="70" r={radius}
            fill="none"
            stroke={colour}
            strokeWidth="11"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            transform="rotate(-90 70 70)"
            style={{ transition: 'stroke-dashoffset 0.6s ease' }}
          />
        </svg>

        <div className="score-gauge__label">
          <span className="score-gauge__number" style={{ color: colour }}>
            {score !== null && score !== undefined ? score : '—'}
          </span>
          <span className="score-gauge__text" style={{ fontSize: '0.7rem' }}>ATS Score</span>
        </div>
      </div>

      <div className="score-tier" style={{ marginTop: '1.25rem', textAlign: 'center' }}>
        <span className={`badge ${tier.class}`} style={{ fontSize: '0.8rem', padding: '0.35rem 0.85rem' }}>
          {tier.label}
        </span>
      </div>
    </div>
  )
}
