import { useEffect, useRef } from 'react'
import { useAppDispatch, useAppSelector } from '../../app/hooks'
import { baseApi } from '../api/baseApi'

type Tag = Parameters<typeof baseApi.util.invalidateTags>[0][number]

/** Subscribe to a server SSE channel and invalidate RTK tags on its change
 *  signal — one long-lived connection instead of a request every N seconds.
 *  EventSource can't send an Authorization header, so the access token rides
 *  a query param. No-ops when signed out; closes on unmount. */
export function useLiveUpdates(channel: string, tags: Tag[]) {
  const token = useAppSelector((s) => s.auth.accessToken)
  const dispatch = useAppDispatch()
  const tagsRef = useRef(tags)
  tagsRef.current = tags

  useEffect(() => {
    if (!token) return
    const source = new EventSource(`/api/events/${channel}?token=${encodeURIComponent(token)}`)
    source.addEventListener('change', () => {
      dispatch(baseApi.util.invalidateTags(tagsRef.current))
    })
    return () => source.close()
  }, [channel, token, dispatch])
}
