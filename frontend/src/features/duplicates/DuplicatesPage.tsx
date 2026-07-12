import { useState } from 'react'
import { Link } from 'react-router-dom'
import { usePagination } from '../../shared/hooks/usePagination'
import { formatDate } from '../../shared/lib/format'
import { Badge } from '../../shared/ui/Badge'
import { Button } from '../../shared/ui/Button'
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog'
import { Select } from '../../shared/ui/Field'
import { Card, EmptyState, PageBody, PageHeader, Spinner } from '../../shared/ui/Page'
import { Pagination } from '../../shared/ui/Pagination'
import { SourceBadge } from '../patients/PatientsPage'
import {
  useDismissDuplicateMutation,
  useDuplicatesQuery,
  useMergeDuplicateMutation,
  useScanDuplicatesMutation,
} from './api'
import type { DuplicateFlag, DuplicatePatient } from './types'

const statusTones = { pending: 'amber', merged: 'green', dismissed: 'muted' } as const

function PatientCell({ patient, label }: { patient: DuplicatePatient; label: string }) {
  return (
    <div className="min-w-0">
      <p className="text-ink-faint text-[10px] font-bold tracking-[0.1em] uppercase">{label}</p>
      <Link to={`/patients/${patient.id}`} className="text-primary text-[13px] font-medium hover:underline">
        {patient.lastName}, {patient.firstName}
      </Link>
      <p className="text-ink-muted text-xs">
        <span className="font-mono">{patient.mrn}</span> · {formatDate(patient.dob)} · {patient.sex}
      </p>
      <div className="mt-1">
        <SourceBadge source={patient.source} />
      </div>
    </div>
  )
}

export function DuplicatesPage() {
  const [status, setStatus] = useState('pending')
  const { limit, offset, setPage, reset } = usePagination()
  const { data, isLoading, isFetching } = useDuplicatesQuery({
    status: status || undefined,
    limit,
    offset,
  })
  const [scan, { isLoading: scanning }] = useScanDuplicatesMutation()
  const [merge, { isLoading: merging }] = useMergeDuplicateMutation()
  const [dismiss] = useDismissDuplicateMutation()
  const [confirming, setConfirming] = useState<DuplicateFlag | null>(null)
  const [scanMessage, setScanMessage] = useState<string | null>(null)

  async function onScan() {
    const result = await scan()
    if ('data' in result && result.data) {
      setScanMessage(
        result.data.newFlags === 0
          ? 'Scan complete — no new duplicate candidates.'
          : `Scan complete — ${result.data.newFlags} new candidate pair${result.data.newFlags === 1 ? '' : 's'} flagged.`,
      )
    }
  }

  return (
    <>
      <PageHeader
        title="Duplicate review"
        actions={
          <Button size="sm" onClick={onScan} disabled={scanning}>
            <i className="iconify tabler--radar-2" aria-hidden />
            {scanning ? 'Scanning…' : 'Scan for duplicates'}
          </Button>
        }
      />
      <PageBody>
        <Card className="mb-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-ink-muted text-[13px]">
              Candidate pairs matched on name and date of birth across sources. Merging moves all
              clinical data onto the surviving record.
              {scanMessage && <span className="text-primary block font-semibold">{scanMessage}</span>}
            </p>
            <div className="w-44">
              <Select
                value={status}
                onChange={(e) => {
                  setStatus(e.target.value)
                  reset()
                }}
              >
                <option value="pending">Pending review</option>
                <option value="merged">Merged</option>
                <option value="dismissed">Dismissed</option>
                <option value="">All</option>
              </Select>
            </div>
          </div>
        </Card>

        {isLoading && <Spinner />}
        {data && data.items.length === 0 && (
          <EmptyState
            icon="tabler--user-check"
            message="No duplicate candidates here. Run a scan after importing new data."
          />
        )}
        {data && data.items.length > 0 && (
          <Card flush className={isFetching ? 'opacity-60' : ''}>
            <ul className="divide-line divide-y">
              {data.items.map((flag) => (
                <li key={flag.id} className="flex flex-wrap items-center gap-4 px-5 py-4">
                  <div className="grid min-w-0 flex-1 grid-cols-1 gap-4 sm:grid-cols-2">
                    <PatientCell patient={flag.patientA} label="Keep" />
                    <PatientCell patient={flag.patientB} label="Candidate duplicate" />
                  </div>
                  <div className="flex w-full flex-col items-end gap-2 sm:w-auto">
                    <Badge tone={statusTones[flag.status]}>{flag.status}</Badge>
                    <p className="text-ink-muted max-w-52 text-right text-xs">{flag.reason}</p>
                    {flag.status === 'pending' && (
                      <div className="flex gap-2">
                        <Button size="sm" variant="secondary" onClick={() => dismiss(flag.id)}>
                          Not a duplicate
                        </Button>
                        <Button size="sm" onClick={() => setConfirming(flag)}>
                          <i className="iconify tabler--arrows-join" aria-hidden /> Merge
                        </Button>
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
            <Pagination total={data.total} limit={limit} offset={offset} onPage={setPage} noun="pair" />
          </Card>
        )}

        {confirming && (
          <ConfirmDialog
            open
            title="Merge records"
            message={`Merge ${confirming.patientB.firstName} ${confirming.patientB.lastName} (${confirming.patientB.mrn}) into ${confirming.patientA.firstName} ${confirming.patientA.lastName} (${confirming.patientA.mrn})? All encounters, observations and appointments move to the surviving record.`}
            confirmLabel="Merge records"
            busy={merging}
            onConfirm={async () => {
              await merge(confirming.id)
              setConfirming(null)
            }}
            onClose={() => setConfirming(null)}
          />
        )}
      </PageBody>
    </>
  )
}
