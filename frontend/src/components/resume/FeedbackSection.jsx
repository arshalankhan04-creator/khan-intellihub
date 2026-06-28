/**
 * Full feedback report display.
 * Renders all sub-sections from the backend feedback_report object in a modern card-based grid layout.
 * Props:
 *   feedbackReport  object — the feedback_report from the API
 */
import { PriorityActions }    from './PriorityActions'
import { SectionSuggestions } from './SectionSuggestions'
import { MissingSkillsTags }  from './MissingSkillsTags'

function BulletList({ items, icon }) {
  if (!items || items.length === 0) return null
  return (
    <ul className="bullet-list">
      {items.map((item, i) => (
        <li key={i} className="bullet-list__item">
          <span className="bullet-list__icon" aria-hidden="true">{icon}</span>
          <span className="bullet-list__text">{item}</span>
        </li>
      ))}
    </ul>
  )
}

export function FeedbackSection({ feedbackReport }) {
  if (!feedbackReport) return null

  const {
    overall_summary,
    top_strengths,
    top_weaknesses,
    priority_actions,
    section_suggestions,
    skills_suggestions,
    experience_suggestions,
    enhancement_tips,
    missing_skills,
  } = feedbackReport

  return (
    <div className="feedback-section">
      
      {/* Card 1: Overview Summary, Strengths & Weaknesses */}
      <div className="card results-card" style={{ display: 'block' }}>
        {overall_summary && (
          <div className="feedback-summary" style={{ marginBottom: '1.75rem' }}>
            <h2 className="section-title">Analysis Summary</h2>
            <p className="feedback-summary__text" style={{ fontSize: '1.02rem', lineHeight: '1.6', color: 'var(--color-text)', opacity: 0.95 }}>
              {overall_summary}
            </p>
          </div>
        )}

        <div className="strengths-weaknesses-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', borderTop: '1px solid var(--color-border)', paddingTop: '1.5rem' }}>
          {/* Strengths Column */}
          {top_strengths?.length > 0 && (
            <div className="feedback-column">
              <h3 className="section-heading" style={{ marginTop: 0, fontSize: '1.1rem', color: 'var(--color-success)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>✓</span> Top Strengths
              </h3>
              <BulletList items={top_strengths} icon="✦" />
            </div>
          )}

          {/* Weaknesses Column */}
          {top_weaknesses?.length > 0 && (
            <div className="feedback-column">
              <h3 className="section-heading" style={{ marginTop: 0, fontSize: '1.1rem', color: 'var(--color-accent)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>✗</span> Areas for Improvement
              </h3>
              <BulletList items={top_weaknesses} icon="✦" />
            </div>
          )}
        </div>
      </div>

      {/* Card 2: Priority Action Steps */}
      <PriorityActions actions={priority_actions} />

      {/* Card 3: Section Improvement Suggestions */}
      <SectionSuggestions suggestions={section_suggestions} />

      {/* Card 4: Detailed Recommendations Grid (Skills, Exp, Enhancement) */}
      {(skills_suggestions?.length > 0 || experience_suggestions?.length > 0 || enhancement_tips?.length > 0) && (
        <div className="card results-card detailed-recommendations" style={{ display: 'block' }}>
          <h2 className="section-title">Detailed Recommendations</h2>
          <p className="section-subtitle-hint">Follow these specific formatting and wording suggestions to polish your content.</p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '2rem', marginTop: '1.5rem' }}>
            {skills_suggestions?.length > 0 && (
              <div className="recommendation-column">
                <h3 className="section-heading" style={{ marginTop: 0, fontSize: '1.1rem', color: 'var(--color-primary)', borderBottom: '1px solid var(--color-border)', paddingBottom: '0.5rem' }}>
                  Skills Optimizations
                </h3>
                <BulletList items={skills_suggestions} icon="⚡" />
              </div>
            )}

            {experience_suggestions?.length > 0 && (
              <div className="recommendation-column">
                <h3 className="section-heading" style={{ marginTop: 0, fontSize: '1.1rem', color: 'var(--color-secondary)', borderBottom: '1px solid var(--color-border)', paddingBottom: '0.5rem' }}>
                  Experience Quality
                </h3>
                <BulletList items={experience_suggestions} icon="💼" />
              </div>
            )}

            {enhancement_tips?.length > 0 && (
              <div className="recommendation-column">
                <h3 className="section-heading" style={{ marginTop: 0, fontSize: '1.1rem', color: 'var(--color-success)', borderBottom: '1px solid var(--color-border)', paddingBottom: '0.5rem' }}>
                  Formatting & Tips
                </h3>
                <BulletList items={enhancement_tips} icon="✦" />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Card 5: Missing Skills Tags */}
      <MissingSkillsTags skills={missing_skills} />

    </div>
  )
}
