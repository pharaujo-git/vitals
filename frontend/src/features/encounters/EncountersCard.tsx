import { useState } from 'react'
import { usePagination } from '../../shared/hooks/usePagination'
import { formatDateTime } from '../../shared/lib/format'
import { Badge } from '../../shared/ui/Badge'
import { Button } from '../../shared/ui/Button'
import { Card, EmptyState, Spinner } from '../../shared/ui/Page'
import { Pagination } from '../../shared/ui/Pagination'
import { SourceBadge } from '../patients/PatientsPage'
import { useEncountersQuery } from './api'
import { EncounterModal } from './EncounterModal'
import { encounterTypeLabels, formatObservationValue, type Encounter } from './types'

function EncounterRow({ encounter }: { encounter: Encounter }) {
  const [open, setOpen] = useState(false)
  return (
    <li>
      <button
        onClick={() => setOpen((v) => !v)}
        className="hover:bg-well/60 flex w-full items-center gap-3 px-5 py-3 text-left transition-colors"
      >
        <i
          className={`iconify ${open ? 'tabler--chevron-down' : 'tabler--chevron-right'} text-ink-faint size-4 shrink-0`}
          aria-hidden
        />
        <div className="min-w-0 flex-1">
          <p className="text-ink text-[13px] font-medium">
            {encounterTypeLabels[encounter.encounterType] ?? encounter.encounterType}
            {encounter.reason ? ` — ${encounter.reason}` : ''}
          </p>
          <p className="text-ink-muted text-xs">
            {formatDateTime(encounter.occurredAt)}
            {encounter.clinicianName ? ` · ${encounter.clinicianName}` : ''}
          </p>
        </div>
        <Badge tone="muted">
          {encounter.observations.length} obs
        </Badge>
        <SourceBadge source={encounter.source} />
      </button>
      {open && (
        <div className="bg-well/40 border-line border-t px-5 py-3 pl-12">
          {encounter.observations.length === 0 && (
            <p className="text-ink-muted text-xs">No observations recorded.</p>
          )}
          {encounter.observations.length > 0 && (
            <table className="w-full text-[12.5px]">
              <tbody className="divide-line/60 divide-y">
                {encounter.observations.map((o) => (
                  <tr key={o.id}>
                    <td className="text-ink-muted py-1.5 pr-4">{o.code.replaceAll('_', ' ')}</td>
                    <td className="text-ink py-1.5 font-medium">{formatObservationValue(o)}</td>
                    <td className="text-ink-faint py-1.5 text-right text-xs">
                      {formatDateTime(o.takenAt)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {encounter.notes && (
            <p className="text-ink-muted mt-2 text-xs whitespace-pre-wrap">{encounter.notes}</p>
          )}
        </div>
      )}
    </li>
  )
}

export function EncountersCard({ patientId, canEdit }: { patientId: string; canEdit: boolean }) {
  const { limit, offset, setPage } = usePagination(10)
  const { data, isLoading } = useEncountersQuery({ patientId, limit, offset })
  const [adding, setAdding] = useState(false)

  return (
    <Card
      title="Encounters"
      flush
      actions={
        canEdit ? (
          <Button size="sm" onClick={() => setAdding(true)}>
            <i className="iconify tabler--plus" aria-hidden /> New encounter
          </Button>
        ) : undefined
      }
    >
      {isLoading && <Spinner />}
      {data && data.items.length === 0 && (
        <div className="p-5">
          <EmptyState icon="tabler--stethoscope" message="No encounters documented yet." />
        </div>
      )}
      {data && data.items.length > 0 && (
        <>
          <ul className="divide-line divide-y">
            {data.items.map((e) => (
              <EncounterRow key={e.id} encounter={e} />
            ))}
          </ul>
          <Pagination
            total={data.total}
            limit={limit}
            offset={offset}
            onPage={setPage}
            noun="encounter"
          />
        </>
      )}
      {adding && <EncounterModal patientId={patientId} onClose={() => setAdding(false)} />}
    </Card>
  )
}
