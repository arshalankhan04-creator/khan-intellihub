/**
 * Central Axios instance for all HTTP communication.
 *
 * Request interceptor  — attaches JWT from localStorage as Bearer token.
 * Response interceptor — on 401, silently refreshes the access token once,
 *                        then retries the original request.
 *                        On refresh failure, clears auth state and redirects.
 */
import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
})

// ── Request interceptor ───────────────────────────────────────────────────
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('kh_access')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ── Response interceptor ─────────────────────────────────────────────────
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Only attempt refresh on 401 and only once per request
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('kh_refresh')
      if (!refreshToken) {
        // No refresh token — clear auth and redirect
        _clearAuth()
        return Promise.reject(error)
      }

      try {
        const response = await axios.post(
          `${import.meta.env.VITE_API_BASE_URL}/api/v1/auth/token/refresh/`,
          { refresh: refreshToken },
        )

        const newAccessToken = response.data.access
        localStorage.setItem('kh_access', newAccessToken)
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`

        return client(originalRequest)
      } catch {
        // Refresh failed — session is expired
        _clearAuth()
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  },
)

function _clearAuth() {
  localStorage.removeItem('kh_access')
  localStorage.removeItem('kh_refresh')
  localStorage.removeItem('kh_email')
  window.location.href = '/login'
}

export default client
