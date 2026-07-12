import { useState } from 'react'
import { usePagination } from '../../shared/hooks/usePagination'
import { formatDateTime } from '../../shared/lib/format'
import { Badge } from '../../shared/ui/Badge'
import { Input, Select } from '../../shared/ui/Field'
import { Card, EmptyState, PageBody, PageHeader, Spinner } from '../../shared/ui/Page'
import { Pagination } from '../../shared/ui/Pagination'
import { useAuditActionsQuery, useAuditEntriesQuery } from './api'

function actionTone(action: string): 'green' | 'blue' | 'amber' | 'red' | 'muted' {
  if (action.endsWith('.created') || action.endsWith('.booked')) return 'green'
  if (action.endsWith('.updated') || action.endsWith('.moved')) return 'amber'
  if (action.endsWith('.denied') || action.endsWith('.cancelled')) return 'red'
  if (action.endsWith('.viewed')) return 'blue'
  return 'muted'
}

export function AuditPage() {
  const [action, setAction] = useState('')
  const [entityId, setEntityId] = useState('')
  const { limit, offset, setPage, reset } = usePagination()
  const { data, isLoading, isFetching } = useAuditEntriesQuery({
    action: action || undefined,
    entityId: entityId.trim() || undefined,
    limit,
    offset,
  })
  const { data: actions } = useAuditActionsQuery()

  return (
    <>
      <PageHeader title="Audit log" />
      <PageBody>
        <Card className="mb-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Select
              label="Action"
              value={action}
              onChange={(e) => {
                setAction(e.target.value)
                reset()
              }}
            >
              <option value="">All actions</option>
              {actions?.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </Select>
            <Input
              label="Entity ID"
              icon="tabler--filter"
              placeholder="Filter by record id…"
              value={entityId}
              onChange={(e) => {
                setEntityId(e.target.value)
                reset()
              }}
            />
          </div>
        </Card>

        {isLoading && <Spinner />}
        {data && data.items.length === 0 && (
          <EmptyState icon="tabler--shield-search" message="No audit entries match." />
        )}
        {data && data.items.length > 0 && (
          <Card flush className={isFetching ? 'opacity-60' : ''}>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="bg-well text-ink-muted border-line border-b text-left text-[10.5px] font-bold tracking-[0.08em] uppercase">
                    <th className="px-5 py-2.5">When</th>
                    <th className="px-5 py-2.5">Who</th>
                    <th className="px-5 py-2.5">Action</th>
                    <th className="px-5 py-2.5">Entity</th>
                    <th className="px-5 py-2.5">Detail</th>
                  </tr>
                </thead>
                <tbody className="divide-line divide-y">
                  {data.items.map((entry) => (
                    <tr key={entry.id} className="hover:bg-well/60 transition-colors">
                      <td className="text-ink-muted px-5 py-2.5 whitespace-nowrap">
                        {formatDateTime(entry.createdAt)}
                      </td>
                      <td className="text-ink px-5 py-2.5">{entry.userEmail}</td>
                      <td className="px-5 py-2.5">
                        <Badge tone={actionTone(entry.action)}>{entry.action}</Badge>
                      </td>
                      <td className="text-ink-muted px-5 py-2.5">
                        {entry.entityType ? (
                          <>
                            {entry.entityType}
                            <span className="text-ink-faint block max-w-40 truncate font-mono text-[11px]">
                              {entry.entityId}
                            </span>
                          </>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="text-ink-muted max-w-60 truncate px-5 py-2.5 font-mono text-[11px]">
                        {entry.detail ? JSON.stringify(entry.detail) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination total={data.total} limit={limit} offset={offset} onPage={setPage} noun="entry" />
          </Card>
        )}
      </PageBody>
    </>
  )
}
