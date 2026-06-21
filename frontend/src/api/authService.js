/**
 * Auth API service.
 * All calls go through the central Axios client.
 */
import client from './axiosClient'

/** Register a new account. Returns { access, refresh, user_id }. */
export function register(email, password) {
  return client.post('/api/v1/auth/register/', { email, password })
    .then(res => res.data)
}

/** Login with existing credentials. Returns { access, refresh }. */
export function login(email, password) {
  return client.post('/api/v1/auth/login/', { email, password })
    .then(res => res.data)
}

/** Exchange a refresh token for a new access token. Returns { access }. */
export function refreshToken(refresh) {
  return client.post('/api/v1/auth/token/refresh/', { refresh })
    .then(res => res.data)
}
