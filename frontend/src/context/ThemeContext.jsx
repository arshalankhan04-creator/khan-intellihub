/**
 * Theme initializer — sets the data-theme attribute and dark class on <html>
 * based on the user's saved preference in localStorage.
 *
 * Call this ONCE before React renders (in main.jsx) so the correct theme
 * is applied immediately and avoids a flash of unstyled content (FOUC).
 *
 * The actual toggle logic lives inside ThemeToggle.jsx — it manages its
 * own local state and DOM mutations, so no React Context is needed.
 */
export function initTheme() {
  const saved = localStorage.getItem('theme') || 'dark'
  const root = document.documentElement
  root.setAttribute('data-theme', saved)
  if (saved === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}
