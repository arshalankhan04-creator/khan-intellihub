import { useContext } from 'react'
import { AuthContext } from '../context/AuthContext'

/** Thin hook wrapper around AuthContext. Use this in all components. */
export function useAuth() {
  return useContext(AuthContext)
}
