/**
 * Four horizontal progress bars — one per scoring category.
 * Props:
 *   scores  { skills_match, section_completeness, experience_quality, content_quality }
 */
import { getScoreHex } from '../../utils/formatters'

const CATEGORIES = [
  { key: 'skills_match',         label: 'Skills Match',          weight: '40%' },
  { key: 'section_completeness', label: 'Section Completeness',  weight: '20%' },
  { key: 'experience_quality',   label: 'Experience Quality',    weight: '20%' },
  { key: 'content_quality',      label: 'Content Quality',       weight: '20%' },
]

export function ScoreBreakdown({ scores }) {
  if (!scores) return null

  return (
    <div className="score-breakdown">
      <h3 className="score-breakdown__title">Category Scores</h3>
      {CATEGORIES.map(({ key, label, weight }) => {
        const value = scores[key]
        const pct = value !== null && value !== undefined
          ? Math.round(value)
          : null

        return (
          <div key={key} className="score-breakdown__row">
            <div className="score-breakdown__meta">
              <span className="score-breakdown__label">{label}</span>
              <span className="score-breakdown__weight">{weight}</span>
              <span className="score-breakdown__value">
                {pct !== null ? `${pct}` : '—'}
              </span>
            </div>
            <div className="score-breakdown__bar-track">
              <div
                className="score-breakdown__bar-fill"
                style={{
                  width: pct !== null ? `${pct}%` : '0%',
                  backgroundColor: getScoreHex(pct),
                  transition: 'width 0.5s ease',
                }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
