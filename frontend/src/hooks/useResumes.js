import { useState, useEffect } from 'react'
import { listResumes } from '../api/resumeService'

/**
 * Data-fetching hook for the paginated resume list.
 * Re-fetches automatically when page or pageSize changes.
 */
export function useResumes(page = 1, pageSize = 10) {
  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)

    listResumes({ page, page_size: pageSize })
      .then(res => {
        if (!cancelled) setData(res)
      })
      .catch(err => {
        if (!cancelled) setError(err)
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => { cancelled = true }
  }, [page, pageSize])

  return { data, isLoading, error, setData }
}
