import { useState } from 'react'
import { usePagination } from '../../shared/hooks/usePagination'
import { formatDateTime } from '../../shared/lib/format'
import { Badge } from '../../shared/ui/Badge'
import { Button } from '../../shared/ui/Button'
import { Card, EmptyState, PageBody, PageHeader, Spinner } from '../../shared/ui/Page'
import { Pagination } from '../../shared/ui/Pagination'
import { useInboxQuery, useSentMessagesQuery, useUnreadCountQuery } from './api'
import { ComposeModal } from './ComposeModal'
import { ThreadModal } from './ThreadModal'
import type { Message } from './types'

type Tab = 'inbox' | 'sent'

function MessageRow({
  message,
  tab,
  onOpen,
}: {
  message: Message
  tab: Tab
  onOpen: () => void
}) {
  const unread = tab === 'inbox' && message.readAt === null
  return (
    <li>
      <button
        onClick={onOpen}
        className="hover:bg-well/60 flex w-full items-center gap-3 px-5 py-3 text-left transition-colors"
      >
        <span
          className={`size-2 shrink-0 rounded-full ${unread ? 'bg-primary' : 'bg-transparent'}`}
          aria-label={unread ? 'Unread' : undefined}
        />
        <div className="min-w-0 flex-1">
          <p className={`truncate text-[13px] ${unread ? 'text-ink font-bold' : 'text-ink font-medium'}`}>
            {message.subject}
          </p>
          <p className="text-ink-muted truncate text-xs">
            {tab === 'inbox' ? `From ${message.senderName}` : `To ${message.recipientName}`}
            {message.body ? ` — ${message.body}` : ''}
          </p>
        </div>
        {message.patientName && (
          <Badge tone="primary">
            <i className="iconify tabler--user size-3" aria-hidden />
            {message.patientName}
          </Badge>
        )}
        <span className="text-ink-faint shrink-0 text-xs whitespace-nowrap">
          {formatDateTime(message.createdAt)}
        </span>
      </button>
    </li>
  )
}

export function MessagesPage() {
  const [tab, setTab] = useState<Tab>('inbox')
  const [unreadOnly, setUnreadOnly] = useState(false)
  const inboxPager = usePagination()
  const sentPager = usePagination()
  const { data: unread } = useUnreadCountQuery()

  const inbox = useInboxQuery(
    { unread: unreadOnly || undefined, limit: inboxPager.limit, offset: inboxPager.offset },
    { skip: tab !== 'inbox' },
  )
  const sent = useSentMessagesQuery(
    { limit: sentPager.limit, offset: sentPager.offset },
    { skip: tab !== 'sent' },
  )

  const [composing, setComposing] = useState(false)
  const [viewing, setViewing] = useState<Message | null>(null)

  const active = tab === 'inbox' ? inbox : sent
  const pager = tab === 'inbox' ? inboxPager : sentPager

  return (
    <>
      <PageHeader
        title="Messages"
        actions={
          <Button size="sm" onClick={() => setComposing(true)}>
            <i className="iconify tabler--pencil-plus" aria-hidden /> New message
          </Button>
        }
      />
      <PageBody>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="bg-well inline-grid grid-cols-2 gap-1 rounded-md p-1">
            {(['inbox', 'sent'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`flex items-center gap-1.5 rounded px-4 py-1.5 text-[13px] font-semibold capitalize transition-colors ${
                  tab === t ? 'bg-surface text-ink shadow-sm' : 'text-ink-muted'
                }`}
              >
                <i
                  className={`iconify ${t === 'inbox' ? 'tabler--inbox' : 'tabler--send'} size-4`}
                  aria-hidden
                />
                {t}
                {t === 'inbox' && (unread?.count ?? 0) > 0 && (
                  <span className="bg-primary rounded-full px-1.5 text-[10.5px] font-bold text-white">
                    {unread?.count}
                  </span>
                )}
              </button>
            ))}
          </div>
          {tab === 'inbox' && (
            <label className="text-ink-muted flex cursor-pointer items-center gap-2 text-[13px]">
              <input
                type="checkbox"
                checked={unreadOnly}
                onChange={(e) => {
                  setUnreadOnly(e.target.checked)
                  inboxPager.reset()
                }}
                className="accent-primary size-3.5"
              />
              Unread only
            </label>
          )}
        </div>

        {active.isLoading && <Spinner />}
        {active.data && active.data.items.length === 0 && (
          <EmptyState
            icon={tab === 'inbox' ? 'tabler--inbox-off' : 'tabler--send-off'}
            message={tab === 'inbox' ? 'Your inbox is empty.' : 'No sent messages yet.'}
          />
        )}
        {active.data && active.data.items.length > 0 && (
          <Card flush className={active.isFetching ? 'opacity-60' : ''}>
            <ul className="divide-line divide-y">
              {active.data.items.map((m) => (
                <MessageRow key={m.id} message={m} tab={tab} onOpen={() => setViewing(m)} />
              ))}
            </ul>
            <Pagination
              total={active.data.total}
              limit={pager.limit}
              offset={pager.offset}
              onPage={pager.setPage}
              noun="message"
            />
          </Card>
        )}

        {composing && <ComposeModal onClose={() => setComposing(false)} />}
        {viewing && <ThreadModal message={viewing} onClose={() => setViewing(null)} />}
      </PageBody>
    </>
  )
}
