/**
 * Registration form.
 * Validates client-side before calling the backend.
 * Surfaces all server errors inline.
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../../api/authService'
import { useAuth } from '../../hooks/useAuth'
import { isValidEmail, isValidPassword } from '../../utils/validators'
import { ErrorMessage } from '../common/ErrorMessage'

export function RegisterForm() {
  const navigate = useNavigate()
  const { login } = useAuth()

  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [isLoading, setIsLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    // Client-side validation
    if (!isValidEmail(email)) {
      setError('Please enter a valid email address.')
      return
    }
    if (!isValidPassword(password)) {
      setError('Password must be at least 8 characters.')
      return
    }

    setIsLoading(true)
    try {
      const data = await register(email, password)
      // register returns { access, refresh, user_id }
      login(data.access, data.refresh, email)
      navigate('/dashboard')
    } catch (err) {
      const code = err.response?.data?.code
      const message = err.response?.data?.error

      if (code === 'EMAIL_EXISTS') {
        setError('An account with this email already exists.')
      } else if (message) {
        setError(message)
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <h1 className="auth-form__title">Create your account</h1>

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
          placeholder="Minimum 8 characters"
          required
          autoComplete="new-password"
          disabled={isLoading}
        />
      </div>

      <button
        type="submit"
        className="btn btn--primary btn--full"
        disabled={isLoading}
      >
        {isLoading ? 'Creating account…' : 'Create account'}
      </button>

      <p className="auth-form__footer">
        Already have an account?{' '}
        <Link to="/login" className="link">Sign in</Link>
      </p>
    </form>
  )
}
