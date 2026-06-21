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

  return (
    <div className="score-gauge">
      <svg width="140" height="140" viewBox="0 0 140 140" aria-hidden="true">
        {/* Background track */}
        <circle
          cx="70" cy="70" r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="12"
        />
        {/* Score arc */}
        <circle
          cx="70" cy="70" r={radius}
          fill="none"
          stroke={colour}
          strokeWidth="12"
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
        <span className="score-gauge__text">ATS Score</span>
      </div>
    </div>
  )
}
