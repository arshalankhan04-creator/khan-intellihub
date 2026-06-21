/**
 * AuthContext — single source of truth for authentication state.
 *
 * Persists access token, refresh token, and user email to localStorage
 * so sessions survive page reloads.
 *
 * The Axios interceptor reads localStorage directly (not React state)
 * to avoid stale closure issues on retried requests.
 */
import { createContext, useState, useEffect } from 'react'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(
    () => localStorage.getItem('kh_access') || null,
  )
  const [refreshToken, setRefreshToken] = useState(
    () => localStorage.getItem('kh_refresh') || null,
  )
  const [userEmail, setUserEmail] = useState(
    () => localStorage.getItem('kh_email') || null,
  )

  const isAuthenticated = !!accessToken

  /**
   * Call after a successful register or login.
   * Stores all three values in state and localStorage.
   */
  function login(access, refresh, email) {
    localStorage.setItem('kh_access', access)
    localStorage.setItem('kh_refresh', refresh)
    localStorage.setItem('kh_email', email)
    setAccessToken(access)
    setRefreshToken(refresh)
    setUserEmail(email)
  }

  /**
   * Clear all auth state and localStorage.
   * Called on manual logout or session expiry.
   */
  function logout() {
    localStorage.removeItem('kh_access')
    localStorage.removeItem('kh_refresh')
    localStorage.removeItem('kh_email')
    setAccessToken(null)
    setRefreshToken(null)
    setUserEmail(null)
  }

  /**
   * Called by the Axios interceptor after a silent token refresh.
   * Updates state and localStorage without touching the refresh token.
   */
  function updateAccessToken(token) {
    localStorage.setItem('kh_access', token)
    setAccessToken(token)
  }

  return (
    <AuthContext.Provider
      value={{
        accessToken,
        refreshToken,
        userEmail,
        isAuthenticated,
        login,
        logout,
        updateAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
