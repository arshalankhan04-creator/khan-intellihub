/**
 * Renders missing skills as pill tags.
 * Renders nothing if the list is empty or null.
 * Props:
 *   skills  string[]
 */
export function MissingSkillsTags({ skills }) {
  if (!skills || skills.length === 0) return null

  return (
    <div className="card results-card missing-skills" style={{ display: 'block' }}>
      <h2 className="section-title">Missing Core Skills</h2>
      <p className="section-subtitle-hint">Crucial skills missing from your resume that are highly relevant to your target domain.</p>
      
      <div className="missing-skills__tags">
        {skills.map((skill, i) => (
          <span key={i} className="skill-tag">{skill}</span>
        ))}
      </div>
    </div>
  )
}
