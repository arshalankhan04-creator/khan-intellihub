import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { initTheme } from './context/ThemeContext'
import './index.css'
import App from './App.jsx'

// Apply saved theme to <html> before first paint to avoid FOUC
initTheme()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
