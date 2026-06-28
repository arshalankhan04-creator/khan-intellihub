/**
 * Login page.
 * Reads the ?next= query param and passes it to LoginForm
 * so the user is redirected to the originally requested route after sign-in.
 */
import { useSearchParams } from 'react-router-dom'
import { LoginForm } from '../components/auth/LoginForm'
import { ThemeToggle } from '../components/common/ThemeToggle'

export function LoginPage() {
  const [searchParams] = useSearchParams()
  const next = searchParams.get('next') || '/dashboard'

  return (
    <div className="auth-page">
      <ThemeToggle floating />
      <div className="auth-card">
        <LoginForm nextPath={next} />
      </div>
    </div>
  )
}
