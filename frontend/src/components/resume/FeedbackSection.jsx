/**
 * Full feedback report display.
 * Renders all sub-sections from the backend feedback_report object.
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
          <span>{item}</span>
        </li>
      ))}
    </ul>
  )
}

function SubSection({ title, items }) {
  if (!items || items.length === 0) return null
  return (
    <div className="feedback-subsection">
      <h3 className="section-heading">{title}</h3>
      <BulletList items={items} icon="→" />
    </div>
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

      {/* Overall Summary */}
      {overall_summary && (
        <div className="feedback-summary">
          <h3 className="section-heading">Overall Summary</h3>
          <p className="feedback-summary__text">{overall_summary}</p>
        </div>
      )}

      {/* Strengths */}
      {top_strengths?.length > 0 && (
        <div className="feedback-subsection">
          <h3 className="section-heading">Top Strengths</h3>
          <BulletList items={top_strengths} icon="✓" />
        </div>
      )}

      {/* Weaknesses */}
      {top_weaknesses?.length > 0 && (
        <div className="feedback-subsection">
          <h3 className="section-heading">Top Weaknesses</h3>
          <BulletList items={top_weaknesses} icon="✗" />
        </div>
      )}

      {/* Priority Actions */}
      <PriorityActions actions={priority_actions} />

      {/* Section Suggestions */}
      <SectionSuggestions suggestions={section_suggestions} />

      {/* Skills Suggestions */}
      <SubSection title="Skills Suggestions" items={skills_suggestions} />

      {/* Experience Suggestions */}
      <SubSection title="Experience Suggestions" items={experience_suggestions} />

      {/* Enhancement Tips */}
      <SubSection title="Enhancement Tips" items={enhancement_tips} />

      {/* Missing Skills Tags */}
      <MissingSkillsTags skills={missing_skills} />

    </div>
  )
}
