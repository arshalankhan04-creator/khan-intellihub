/**
 * Registration page — renders RegisterForm inside a centred card layout.
 * Accessible only to guests (PublicRoute handles the redirect for authed users).
 */
import { RegisterForm } from '../components/auth/RegisterForm'

export function RegisterPage() {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <RegisterForm />
      </div>
    </div>
  )
}
