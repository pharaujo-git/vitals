import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { formatDateTime } from '../../shared/lib/format'
import { Spinner } from '../../shared/ui/Page'
import {
  useMarkNotificationsReadMutation,
  useNotificationUnreadCountQuery,
  useNotificationsQuery,
  type AppNotification,
} from './api'

const kindMeta: Record<string, { icon: string; tone: string }> = {
  appointment: { icon: 'tabler--calendar-time', tone: 'bg-accent-blue/15 text-accent-blue' },
  risk: { icon: 'tabler--alert-triangle', tone: 'bg-accent-red/15 text-accent-red' },
}

function Item({ notification, onGo }: { notification: AppNotification; onGo: () => void }) {
  const meta = kindMeta[notification.kind] ?? {
    icon: 'tabler--bell',
    tone: 'bg-primary/15 text-primary',
  }
  return (
    <button
      onClick={onGo}
      disabled={!notification.link}
      className="hover:bg-well flex w-full items-start gap-2.5 px-4 py-2.5 text-left disabled:cursor-default"
    >
      <span className={`mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full ${meta.tone}`}>
        <i className={`iconify ${meta.icon} size-3.5`} aria-hidden />
      </span>
      <span className="min-w-0">
        <span
          className={`block truncate text-[13px] ${
            notification.readAt === null ? 'text-ink font-bold' : 'text-ink font-medium'
          }`}
        >
          {notification.title}
        </span>
        {notification.body && (
          <span className="text-ink-muted block truncate text-xs">{notification.body}</span>
        )}
        <span className="text-ink-faint block text-[11px]">{formatDateTime(notification.createdAt)}</span>
      </span>
    </button>
  )
}

/** Topbar bell: unread badge, dropdown of recent notifications. Opening the
 *  dropdown marks everything read (SSE keeps the badge live). */
export function NotificationsBell() {
  const [open, setOpen] = useState(false)
  const boxRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const { data: unread } = useNotificationUnreadCountQuery()
  const { data, isLoading } = useNotificationsQuery({ limit: 10 }, { skip: !open })
  const [markRead] = useMarkNotificationsReadMutation()

  useEffect(() => {
    if (!open) return
    function onClick(e: MouseEvent) {
      if (!boxRef.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  function toggle() {
    setOpen((v) => {
      if (!v && (unread?.count ?? 0) > 0) markRead()
      return !v
    })
  }

  return (
    <div ref={boxRef} className="relative">
      <button
        onClick={toggle}
        className="text-ink-muted hover:bg-well hover:text-ink relative flex size-9 items-center justify-center rounded-full transition-colors"
        aria-label="Notifications"
      >
        <i className="iconify tabler--bell text-[19px]" aria-hidden />
        {(unread?.count ?? 0) > 0 && (
          <span className="bg-accent-red absolute top-1 right-1 flex size-4 items-center justify-center rounded-full text-[9.5px] font-bold text-white">
            {unread!.count > 9 ? '9+' : unread!.count}
          </span>
        )}
      </button>
      {open && (
        <div className="bg-surface border-line absolute right-0 mt-1.5 w-80 rounded-lg border py-1.5 shadow-lg">
          <p className="text-ink border-line border-b px-4 pt-1 pb-2 text-sm font-semibold">
            Notifications
          </p>
          {isLoading && <Spinner />}
          {data && data.items.length === 0 && (
            <p className="text-ink-muted px-4 py-6 text-center text-[13px]">
              Nothing yet — appointment changes and risk alerts land here.
            </p>
          )}
          {data && data.items.length > 0 && (
            <ul className="divide-line/60 max-h-96 divide-y overflow-y-auto">
              {data.items.map((notification) => (
                <li key={notification.id}>
                  <Item
                    notification={notification}
                    onGo={() => {
                      setOpen(false)
                      if (notification.link) navigate(notification.link)
                    }}
                  />
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
