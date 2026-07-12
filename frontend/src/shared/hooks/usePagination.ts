import { useState } from 'react'

/** Offset-based pagination state for server-paginated grids. */
export function usePagination(pageSize = 20) {
  const [offset, setOffset] = useState(0)
  return {
    limit: pageSize,
    offset,
    setPage: (next: number) => setOffset(Math.max(next, 0)),
    /** Call whenever a filter changes so you don't land on an out-of-range page. */
    reset: () => setOffset(0),
  }
}
