/**
 * Top navigation bar — rendered on all authenticated pages.
 * Reads user email from AuthContext and provides logout.
 */
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

export function Navbar() {
  const { userEmail, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <nav className="navbar">
      <div className="navbar__brand">
        <Link to="/dashboard" className="navbar__logo">Khan IntelliHub</Link>
      </div>

      <div className="navbar__links">
        <Link to="/dashboard" className="navbar__link">Dashboard</Link>
        <Link to="/upload"    className="navbar__link">Upload</Link>
        <Link to="/history"   className="navbar__link">History</Link>
      </div>

      <div className="navbar__user">
        <span className="navbar__email">{userEmail}</span>
        <button
          type="button"
          className="btn btn--secondary btn--sm"
          onClick={handleLogout}
        >
          Logout
        </button>
      </div>
    </nav>
  )
}
