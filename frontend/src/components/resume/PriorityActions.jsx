/**
 * Priority Actions — groups actions into collapsible high / medium / low sections.
 * Props:
 *   actions  [{ priority: 'high'|'medium'|'low', action: string }]
 */

const PRIORITY_CONFIG = {
  high:   { label: 'High Priority',   borderColor: '#ef4444', bgColor: '#fef2f2' },
  medium: { label: 'Medium Priority', borderColor: '#f97316', bgColor: '#fff7ed' },
  low:    { label: 'Low Priority',    borderColor: '#9ca3af', bgColor: '#f9fafb' },
}

export function PriorityActions({ actions }) {
  if (!actions || actions.length === 0) return null

  const grouped = {
    high:   actions.filter(a => a.priority === 'high'),
    medium: actions.filter(a => a.priority === 'medium'),
    low:    actions.filter(a => a.priority === 'low'),
  }

  return (
    <div className="card results-card priority-actions" style={{ display: 'block' }}>
      <h2 className="section-title">Priority Actions</h2>
      <p className="section-subtitle-hint">Focus on these high-impact tasks to optimize your ATS score.</p>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', marginTop: '1.25rem' }}>
        {Object.entries(grouped).map(([priority, items]) => {
          if (items.length === 0) return null
          const config = PRIORITY_CONFIG[priority]

          return (
            <details key={priority} open={priority === 'high'} className="priority-group">
              <summary className="priority-group__summary">
                <span
                  className="priority-badge"
                  style={{ backgroundColor: config.borderColor }}
                >
                  {config.label}
                </span>
                <span className="priority-group__count">{items.length} Tasks</span>
              </summary>
              <div className="priority-group__items">
                {items.map((item, i) => (
                  <div
                    key={i}
                    className="priority-card"
                    style={{
                      borderLeftColor: config.borderColor,
                      backgroundColor: 'var(--color-surface-hover)',
                    }}
                  >
                    {item.action}
                  </div>
                ))}
              </div>
            </details>
          )
        })}
      </div>
    </div>
  )
}
