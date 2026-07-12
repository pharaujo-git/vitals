import { useState, type FormEvent } from 'react'
import { usePatientsQuery } from '../patients/api'
import { Button } from '../../shared/ui/Button'
import { Input, Label, Select } from '../../shared/ui/Field'
import { Modal } from '../../shared/ui/Modal'
import { ErrorNote } from '../../shared/ui/Page'
import { todayIso } from '../../shared/lib/format'
import {
  useBookAppointmentMutation,
  useCliniciansQuery,
  useLazyNextFreeSlotQuery,
  useRescheduleAppointmentMutation,
} from './api'
import type { Appointment } from './types'

function toLocalParts(iso: string): { date: string; time: string } {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return {
    date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
    time: `${pad(d.getHours())}:${pad(d.getMinutes())}`,
  }
}

export function AppointmentModal({
  appointment,
  defaultDay,
  onClose,
}: {
  appointment: Appointment | null
  defaultDay?: string
  onClose: () => void
}) {
  const start = appointment ? toLocalParts(appointment.startAt) : null
  const end = appointment ? toLocalParts(appointment.endAt) : null

  const [patientSearch, setPatientSearch] = useState('')
  const [patientId, setPatientId] = useState(appointment?.patientId ?? '')
  const [clinicianId, setClinicianId] = useState(appointment?.clinicianId ?? '')
  const [date, setDate] = useState(start?.date ?? defaultDay ?? todayIso())
  const [startTime, setStartTime] = useState(start?.time ?? '09:00')
  const [endTime, setEndTime] = useState(end?.time ?? '09:30')
  const [reason, setReason] = useState(appointment?.reason ?? '')

  const { data: clinicians } = useCliniciansQuery()
  const { data: patients } = usePatientsQuery(
    { search: patientSearch || undefined, limit: 20 },
    { skip: appointment !== null },
  )

  const [book, { isLoading: booking, error: bookError }] = useBookAppointmentMutation()
  const [reschedule, { isLoading: moving, error: moveError }] = useRescheduleAppointmentMutation()
  const [findSlot, { isFetching: finding, error: slotError }] = useLazyNextFreeSlotQuery()
  const error = bookError ?? moveError ?? slotError

  async function onFindSlot() {
    if (!clinicianId) return
    const durationMs = new Date(`${date}T${endTime}:00`).getTime() - new Date(`${date}T${startTime}:00`).getTime()
    const duration = Math.max(Math.round(durationMs / 60000), 15)
    const result = await findSlot({ clinicianId, duration, day: date })
    if (result.data) {
      const start = toLocalParts(result.data.startAt)
      const end = toLocalParts(result.data.endAt)
      setDate(start.date)
      setStartTime(start.time)
      setEndTime(end.time)
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!patientId || !clinicianId) return
    const input = {
      patientId,
      clinicianId,
      startAt: new Date(`${date}T${startTime}:00`).toISOString(),
      endAt: new Date(`${date}T${endTime}:00`).toISOString(),
      reason: reason.trim() || null,
    }
    const result = appointment ? await reschedule({ id: appointment.id, ...input }) : await book(input)
    if (!('error' in result)) onClose()
  }

  return (
    <Modal title={appointment ? 'Move appointment' : 'Book appointment'} open onClose={onClose}>
      <form onSubmit={onSubmit} className="space-y-4">
        {appointment ? (
          <div>
            <Label>Patient</Label>
            <p className="text-ink bg-well rounded-md px-3 py-2 text-[13px]">
              {appointment.patientName}{' '}
              <span className="text-ink-muted font-mono text-xs">{appointment.patientMrn}</span>
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <Input
              label="Patient"
              icon="tabler--search"
              placeholder="Search by name or identifier…"
              value={patientSearch}
              onChange={(e) => setPatientSearch(e.target.value)}
            />
            <Select required value={patientId} onChange={(e) => setPatientId(e.target.value)}>
              <option value="" disabled>
                {patients?.items.length ? 'Choose a patient…' : 'No matching patients'}
              </option>
              {patients?.items.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.lastName}, {p.firstName} ({p.mrn})
                </option>
              ))}
            </Select>
          </div>
        )}
        <Select
          label="Clinician"
          required
          value={clinicianId}
          onChange={(e) => setClinicianId(e.target.value)}
        >
          <option value="" disabled>
            Choose a clinician…
          </option>
          {clinicians?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.displayName}
            </option>
          ))}
        </Select>
        <div className="grid grid-cols-3 gap-3">
          <Input label="Date" type="date" required value={date} onChange={(e) => setDate(e.target.value)} />
          <Input
            label="Start"
            type="time"
            required
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
          />
          <Input
            label="End"
            type="time"
            required
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
          />
        </div>
        <div className="flex justify-end">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={!clinicianId || finding}
            onClick={onFindSlot}
            title="Jump to the clinician's first open slot of this length (searches up to two weeks)"
          >
            <i className="iconify tabler--wand" aria-hidden />
            {finding ? 'Searching…' : 'Find next free slot'}
          </Button>
        </div>
        <Input
          label="Reason (optional)"
          placeholder="Follow-up, annual physical…"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        {error !== undefined && <ErrorNote error={error} />}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={booking || moving || !patientId || !clinicianId}>
            {appointment ? 'Save' : 'Book'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
