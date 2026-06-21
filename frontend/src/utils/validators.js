/**
 * Client-side validation helpers.
 * Called before form submissions to catch obvious errors early.
 */

/** Returns true if the string looks like a valid email address. */
export function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

/** Returns true if the password meets the minimum length requirement (8 chars). */
export function isValidPassword(password) {
  return typeof password === 'string' && password.length >= 8
}
