/**
 * Login form.
 * Supports a ?next= redirect param passed down from the page.
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login as loginApi } from '../../api/authService'
import { useAuth } from '../../hooks/useAuth'
import { isValidEmail } from '../../utils/validators'
import { ErrorMessage } from '../common/ErrorMessage'

export function LoginForm({ nextPath = '/dashboard' }) {
  const navigate = useNavigate()
  const { login } = useAuth()

  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [isLoading, setIsLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (!isValidEmail(email) || !password) {
      setError('Please enter your email and password.')
      return
    }

    setIsLoading(true)
    try {
      const data = await loginApi(email, password)
      // login returns { access, refresh } — email comes from the form
      login(data.access, data.refresh, email)
      navigate(nextPath)
    } catch (err) {
      const code = err.response?.data?.code
      if (code === 'INVALID_CREDENTIALS') {
        setError('Invalid email or password.')
      } else if (err.response?.data?.error) {
        setError(err.response.data.error)
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <h1 className="auth-form__title">Sign in</h1>

      <ErrorMessage message={error} onDismiss={() => setError('')} />

      <div className="form-group">
        <label htmlFor="email" className="form-label">Email</label>
        <input
          id="email"
          type="email"
          className="form-input"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="you@example.com"
          required
          autoComplete="email"
          disabled={isLoading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="password" className="form-label">Password</label>
        <input
          id="password"
          type="password"
          className="form-input"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="Your password"
          required
          autoComplete="current-password"
          disabled={isLoading}
        />
      </div>

      <button
        type="submit"
        className="btn btn--primary btn--full"
        disabled={isLoading}
      >
        {isLoading ? 'Signing in…' : 'Sign in'}
      </button>

      <p className="auth-form__footer">
        Don't have an account?{' '}
        <Link to="/register" className="link">Register</Link>
      </p>
    </form>
  )
}
