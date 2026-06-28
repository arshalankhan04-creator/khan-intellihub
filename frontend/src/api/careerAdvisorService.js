/**
 * Career Advisor API service.
 * All calls go through the central Axios client.
 */
import client from './axiosClient'

/**
 * Generate career advice.
 * @param {string|null} resumeId - UUID of the resume record (or null for manual mode).
 * @param {string} targetRole - Target job role.
 * @param {string} location - Location.
 * @param {string[]} skills - Array of manual skills (used only in manual mode).
 * @returns {Promise} Resolved with advice record data.
 */
export function generateAdvice(resumeId, targetRole, location, skills = []) {
  const payload = {
    target_role: targetRole,
    location: location,
  }
  
  if (resumeId) {
    payload.resume_id = resumeId
  } else {
    payload.skills = skills
  }

  return client.post('/api/v1/career-advisor/generate/', payload)
    .then(res => res.data)
}

/**
 * Fetch career advice results by record UUID.
 * @param {string} recordId - UUID of the career advisor record.
 * @returns {Promise} Resolved with advice record data.
 */
export function getAdviceResults(recordId) {
  return client.get(`/api/v1/career-advisor/${recordId}/results/`)
    .then(res => res.data)
}

/**
 * Fetch career advice history (paginated).
 * @param {{ page: number, page_size: number }} params
 * @returns {Promise} Resolved with { total_count, page, page_size, results }
 */
export function getAdviceHistory({ page = 1, page_size = 10 } = {}) {
  return client.get('/api/v1/career-advisor/history/', { params: { page, page_size } })
    .then(res => res.data)
}
