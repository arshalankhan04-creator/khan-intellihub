/**
 * Public landing page — accessible to unauthenticated visitors.
 * Explains the product and drives sign-up.
 */
import { Link } from 'react-router-dom'

export function LandingPage() {
  return (
    <div className="landing">
      {/* Hero */}
      <header className="landing__hero">
        <h1 className="landing__title">Khan IntelliHub</h1>
        <p className="landing__subtitle">
          AI-powered resume analysis. Get your ATS score and actionable feedback in seconds.
        </p>
        <div className="landing__cta">
          <Link to="/register" className="btn btn--primary btn--lg">
            Get Started — It's Free
          </Link>
          <Link to="/login" className="btn btn--secondary btn--lg">
            Sign In
          </Link>
        </div>
      </header>

      {/* Features */}
      <section className="landing__features">
        <div className="feature-card">
          <span className="feature-card__icon">📄</span>
          <h3 className="feature-card__title">Upload Your Resume</h3>
          <p className="feature-card__desc">
            Submit a PDF and our pipeline extracts structured content instantly — no setup required.
          </p>
        </div>
        <div className="feature-card">
          <span className="feature-card__icon">📊</span>
          <h3 className="feature-card__title">Get Your ATS Score</h3>
          <p className="feature-card__desc">
            Receive a 0–100 ATS compatibility score based on four weighted categories: skills, sections, experience, and content.
          </p>
        </div>
        <div className="feature-card">
          <span className="feature-card__icon">✅</span>
          <h3 className="feature-card__title">Actionable Feedback</h3>
          <p className="feature-card__desc">
            Get prioritised actions, section-by-section suggestions, missing skills, and enhancement tips.
          </p>
        </div>
      </section>

      <footer className="landing__footer">
        <p>Khan IntelliHub © {new Date().getFullYear()}</p>
      </footer>
    </div>
  )
}
