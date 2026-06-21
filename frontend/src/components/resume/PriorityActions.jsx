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
    <div className="priority-actions">
      <h3 className="section-heading">Priority Actions</h3>
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
              <span className="priority-group__count">{items.length}</span>
            </summary>
            <div className="priority-group__items">
              {items.map((item, i) => (
                <div
                  key={i}
                  className="priority-card"
                  style={{
                    borderLeftColor: config.borderColor,
                    backgroundColor: config.bgColor,
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
  )
}
