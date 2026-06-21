/**
 * Resume API service.
 * All calls go through the central Axios client.
 */
import client from './axiosClient'

/**
 * Upload a PDF resume.
 * @param {File} file - The PDF File object.
 * @param {string|null} jobDescription - Optional job description text.
 * @returns {Promise} Resolved with the response data { resume_id, status, ... }
 */
export function uploadResume(file, jobDescription) {
  const formData = new FormData()
  formData.append('file', file)
  if (jobDescription && jobDescription.trim()) {
    formData.append('job_description', jobDescription.trim())
  }
  return client.post('/api/v1/resumes/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(res => res.data)
}

/**
 * Fetch the authenticated user's paginated resume history.
 * @param {{ page: number, page_size: number }} params
 * @returns {Promise} Resolved with { total_count, page, page_size, results }
 */
export function listResumes({ page = 1, page_size = 10 } = {}) {
  return client.get('/api/v1/resumes/', { params: { page, page_size } })
    .then(res => res.data)
}

/**
 * Fetch the full analysis results for a single resume.
 * @param {string} resumeId - UUID of the resume record.
 * @returns {Promise} Resolved with the full result object.
 */
export function getResults(resumeId) {
  return client.get(`/api/v1/resumes/${resumeId}/results/`)
    .then(res => res.data)
}

/**
 * Delete a resume and its associated file from storage.
 * @param {string} resumeId - UUID of the resume record.
 * @returns {Promise} Resolves on 204.
 */
export function deleteResume(resumeId) {
  return client.delete(`/api/v1/resumes/${resumeId}/`)
    .then(res => res.data)
}
