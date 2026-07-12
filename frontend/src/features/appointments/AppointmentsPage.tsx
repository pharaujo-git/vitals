import { useState } from 'react'
import { Link } from 'react-router-dom'
import { usePagination } from '../../shared/hooks/usePagination'
import { formatDate, formatTime, todayIso } from '../../shared/lib/format'
import { Badge } from '../../shared/ui/Badge'
import { Button } from '../../shared/ui/Button'
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog'
import { Input, Select } from '../../shared/ui/Field'
import { Card, EmptyState, PageBody, PageHeader, Spinner } from '../../shared/ui/Page'
import { Pagination } from '../../shared/ui/Pagination'
import {
  useAppointmentsQuery,
  useCliniciansQuery,
  useSetAppointmentStatusMutation,
} from './api'
import { AppointmentModal } from './AppointmentModal'
import type { Appointment, AppointmentStatus } from './types'

const statusTones: Record<AppointmentStatus, 'blue' | 'green' | 'red'> = {
  booked: 'blue',
  completed: 'green',
  cancelled: 'red',
}

function shiftDay(day: string, delta: number): string {
  const d = new Date(`${day}T00:00:00`)
  d.setDate(d.getDate() + delta)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function AppointmentsPage() {
  const [day, setDay] = useState(todayIso())
  const [clinicianId, setClinicianId] = useState('')
  const [status, setStatus] = useState('')
  const { limit, offset, setPage, reset } = usePagination(50)
  const { data, isLoading, isFetching } = useAppointmentsQuery({
    day,
    clinicianId: clinicianId || undefined,
    status: status || undefined,
    limit,
    offset,
  })
  const { data: clinicians } = useCliniciansQuery()
  const [editing, setEditing] = useState<Appointment | 'new' | null>(null)
  const [cancelling, setCancelling] = useState<Appointment | null>(null)
  const [setAppointmentStatus, { isLoading: settingStatus }] = useSetAppointmentStatusMutation()

  return (
    <>
      <PageHeader
        title="Appointments"
        actions={
          <Button size="sm" onClick={() => setEditing('new')}>
            <i className="iconify tabler--plus" aria-hidden /> Book appointment
          </Button>
        }
      />
      <PageBody>
        <Card className="mb-4">
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex items-end gap-1.5">
              <Button
                variant="secondary"
                size="sm"
                className="h-9"
                onClick={() => {
                  setDay(shiftDay(day, -1))
                  reset()
                }}
                aria-label="Previous day"
              >
                <i className="iconify tabler--chevron-left" aria-hidden />
              </Button>
              <div className="w-40">
                <Input
                  label="Day"
                  type="date"
                  value={day}
                  onChange={(e) => {
                    setDay(e.target.value)
                    reset()
                  }}
                />
              </div>
              <Button
                variant="secondary"
                size="sm"
                className="h-9"
                onClick={() => {
                  setDay(shiftDay(day, 1))
                  reset()
                }}
                aria-label="Next day"
              >
                <i className="iconify tabler--chevron-right" aria-hidden />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-9"
                onClick={() => {
                  setDay(todayIso())
                  reset()
                }}
              >
                Today
              </Button>
            </div>
            <div className="w-52">
              <Select
                label="Clinician"
                value={clinicianId}
                onChange={(e) => {
                  setClinicianId(e.target.value)
                  reset()
                }}
              >
                <option value="">All clinicians</option>
                {clinicians?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.displayName}
                  </option>
                ))}
              </Select>
            </div>
            <div className="w-40">
              <Select
                label="Status"
                value={status}
                onChange={(e) => {
                  setStatus(e.target.value)
                  reset()
                }}
              >
                <option value="">All statuses</option>
                <option value="booked">Booked</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </Select>
            </div>
          </div>
        </Card>

        {isLoading && <Spinner />}
        {data && data.items.length === 0 && (
          <EmptyState
            icon="tabler--calendar-off"
            message={`No appointments on ${formatDate(day)}.`}
          />
        )}
        {data && data.items.length > 0 && (
          <Card flush className={isFetching ? 'opacity-60' : ''}>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="bg-well text-ink-muted border-line border-b text-left text-[10.5px] font-bold tracking-[0.08em] uppercase">
                    <th className="px-5 py-2.5">Time</th>
                    <th className="px-5 py-2.5">Patient</th>
                    <th className="px-5 py-2.5">Clinician</th>
                    <th className="px-5 py-2.5">Reason</th>
                    <th className="px-5 py-2.5">Status</th>
                    <th className="px-2 py-2.5" />
                  </tr>
                </thead>
                <tbody className="divide-line divide-y">
                  {data.items.map((a) => (
                    <tr key={a.id} className="hover:bg-well/60 transition-colors">
                      <td className="text-ink px-5 py-2.5 font-medium whitespace-nowrap">
                        {formatTime(a.startAt)} – {formatTime(a.endAt)}
                      </td>
                      <td className="px-5 py-2.5">
                        <Link to={`/patients/${a.patientId}`} className="text-primary hover:underline">
                          {a.patientName}
                        </Link>
                        <span className="text-ink-muted block font-mono text-xs">{a.patientMrn}</span>
                      </td>
                      <td className="text-ink-muted px-5 py-2.5">{a.clinicianName}</td>
                      <td className="text-ink-muted px-5 py-2.5">{a.reason ?? '—'}</td>
                      <td className="px-5 py-2.5">
                        <Badge tone={statusTones[a.status]}>{a.status}</Badge>
                      </td>
                      <td className="px-2 py-2.5 whitespace-nowrap">
                        {a.status === 'booked' && (
                          <div className="flex justify-end gap-0.5">
                            <button
                              onClick={() => setAppointmentStatus({ id: a.id, status: 'completed' })}
                              disabled={settingStatus}
                              className="text-ink-muted hover:bg-accent-green/10 hover:text-accent-green flex size-7 items-center justify-center rounded-md"
                              aria-label="Mark completed"
                              title="Mark completed"
                            >
                              <i className="iconify tabler--check size-4" aria-hidden />
                            </button>
                            <button
                              onClick={() => setEditing(a)}
                              className="text-ink-muted hover:bg-well hover:text-ink flex size-7 items-center justify-center rounded-md"
                              aria-label="Move"
                              title="Move / reschedule"
                            >
                              <i className="iconify tabler--calendar-repeat size-4" aria-hidden />
                            </button>
                            <button
                              onClick={() => setCancelling(a)}
                              className="text-ink-muted hover:bg-accent-red/10 hover:text-accent-red flex size-7 items-center justify-center rounded-md"
                              aria-label="Cancel"
                              title="Cancel"
                            >
                              <i className="iconify tabler--x size-4" aria-hidden />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              total={data.total}
              limit={limit}
              offset={offset}
              onPage={setPage}
              noun="appointment"
            />
          </Card>
        )}

        {editing && (
          <AppointmentModal
            appointment={editing === 'new' ? null : editing}
            defaultDay={day}
            onClose={() => setEditing(null)}
          />
        )}
        {cancelling && (
          <ConfirmDialog
            open
            title="Cancel appointment"
            message={`Cancel ${cancelling.patientName}'s appointment at ${formatTime(cancelling.startAt)}?`}
            confirmLabel="Cancel appointment"
            busy={settingStatus}
            onConfirm={async () => {
              await setAppointmentStatus({ id: cancelling.id, status: 'cancelled' })
              setCancelling(null)
            }}
            onClose={() => setCancelling(null)}
          />
        )}
      </PageBody>
    </>
  )
}
