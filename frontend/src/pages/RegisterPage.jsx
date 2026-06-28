/**
 * Registration page — renders RegisterForm inside a centred card layout.
 * Accessible only to guests (PublicRoute handles the redirect for authed users).
 */
import { RegisterForm } from '../components/auth/RegisterForm'
import { ThemeToggle } from '../components/common/ThemeToggle'

export function RegisterPage() {
  return (
    <div className="auth-page">
      <ThemeToggle floating />
      <div className="auth-card">
        <RegisterForm />
      </div>
    </div>
  )
}
