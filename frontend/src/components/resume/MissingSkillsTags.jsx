/**
 * Renders missing skills as pill tags.
 * Renders nothing if the list is empty or null.
 * Props:
 *   skills  string[]
 */
export function MissingSkillsTags({ skills }) {
  if (!skills || skills.length === 0) return null

  return (
    <div className="missing-skills">
      <h3 className="section-heading">Missing Skills</h3>
      <div className="missing-skills__tags">
        {skills.map((skill, i) => (
          <span key={i} className="skill-tag">{skill}</span>
        ))}
      </div>
    </div>
  )
}
