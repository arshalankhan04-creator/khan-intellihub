/**
 * Per-section improvement suggestions.
 * Only renders cards for sections with non-null suggestions.
 * Props:
 *   suggestions  { contact, skills, education, experience, projects, certifications }
 */

const SECTION_KEYS = [
  'contact', 'skills', 'education', 'experience', 'projects', 'certifications',
]

export function SectionSuggestions({ suggestions }) {
  if (!suggestions) return null

  const activeSections = SECTION_KEYS.filter(key => suggestions[key])
  if (activeSections.length === 0) return null

  return (
    <div className="card results-card section-suggestions" style={{ display: 'block' }}>
      <h2 className="section-title">Section Recommendations</h2>
      <p className="section-subtitle-hint">Targeted feedback to optimize specific sections of your resume.</p>
      
      <div className="section-suggestions__grid">
        {activeSections.map(key => (
          <div key={key} className="suggestion-card">
            <h4 className="suggestion-card__title" style={{ textTransform: 'capitalize' }}>
              {key} Section
            </h4>
            <p className="suggestion-card__body">{suggestions[key]}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
