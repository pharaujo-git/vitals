import { usePagination } from '../../shared/hooks/usePagination'
import { formatDateTime } from '../../shared/lib/format'
import { Card, EmptyState, Spinner } from '../../shared/ui/Page'
import { Pagination } from '../../shared/ui/Pagination'
import { SourceBadge } from '../patients/PatientsPage'
import { useTimelineQuery, type TimelineEvent } from './api'

const kindMeta: Record<TimelineEvent['kind'], { icon: string; tone: string }> = {
  encounter: { icon: 'tabler--stethoscope', tone: 'bg-primary/15 text-primary' },
  appointment: { icon: 'tabler--calendar-time', tone: 'bg-accent-blue/15 text-accent-blue' },
  problem: { icon: 'tabler--clipboard-heart', tone: 'bg-accent-amber/20 text-accent-amber' },
  medication: { icon: 'tabler--pill', tone: 'bg-accent-violet/15 text-accent-violet' },
  allergy: { icon: 'tabler--alert-octagon', tone: 'bg-accent-red/15 text-accent-red' },
}

/** Everything that happened to this patient, newest first, across all features. */
export function TimelineCard({ patientId }: { patientId: string }) {
  const { limit, offset, setPage } = usePagination(10)
  const { data, isLoading } = useTimelineQuery({ patientId, limit, offset })

  return (
    <Card title="Timeline" flush>
      {isLoading && <Spinner />}
      {data && data.items.length === 0 && (
        <div className="p-5">
          <EmptyState icon="tabler--timeline" message="Nothing recorded for this patient yet." />
        </div>
      )}
      {data && data.items.length > 0 && (
        <>
          <ul className="px-5 py-4">
            {data.items.map((event, i) => {
              const meta = kindMeta[event.kind]
              return (
                <li key={`${event.kind}-${event.at}-${i}`} className="relative flex gap-3.5 pb-4 last:pb-0">
                  {i < data.items.length - 1 && (
                    <span className="bg-line absolute top-8 left-[15px] h-[calc(100%-28px)] w-px" />
                  )}
                  <span
                    className={`z-10 flex size-8 shrink-0 items-center justify-center rounded-full ${meta.tone}`}
                  >
                    <i className={`iconify ${meta.icon} size-4`} aria-hidden />
                  </span>
                  <div className="min-w-0 flex-1 pt-0.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-ink text-[13px] font-medium">{event.title}</p>
                      {event.source && event.source !== 'manual' && <SourceBadge source={event.source} />}
                    </div>
                    <p className="text-ink-muted text-xs">
                      {event.detail ? `${event.detail} · ` : ''}
                      {formatDateTime(event.at)}
                    </p>
                  </div>
                </li>
              )
            })}
          </ul>
          <Pagination total={data.total} limit={limit} offset={offset} onPage={setPage} noun="event" />
        </>
      )}
    </Card>
  )
}
