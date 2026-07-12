import { useState } from 'react'
import { formatTime, todayIso } from '../../shared/lib/format'
import { Button } from '../../shared/ui/Button'
import { Select } from '../../shared/ui/Field'
import { Card, Spinner } from '../../shared/ui/Page'
import { useCliniciansQuery, useWeekAppointmentsQuery } from './api'
import type { Appointment, AppointmentStatus } from './types'

const OPEN_HOUR = 8
const CLOSE_HOUR = 18
const HOUR_PX = 52

const blockTones: Record<AppointmentStatus, string> = {
  booked: 'bg-primary/15 border-primary/40 text-primary',
  completed: 'bg-accent-green/15 border-accent-green/40 text-accent-green',
  cancelled: 'bg-well border-line text-ink-faint line-through',
}

function mondayOf(dayIso: string): string {
  const d = new Date(`${dayIso}T00:00:00`)
  const shift = (d.getDay() + 6) % 7 // Monday = 0
  d.setDate(d.getDate() - shift)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function addDays(dayIso: string, delta: number): string {
  const d = new Date(`${dayIso}T00:00:00`)
  d.setDate(d.getDate() + delta)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function Block({ appointment, onOpen }: { appointment: Appointment; onOpen: () => void }) {
  const start = new Date(appointment.startAt)
  const end = new Date(appointment.endAt)
  const top = (start.getHours() + start.getMinutes() / 60 - OPEN_HOUR) * HOUR_PX
  const height = Math.max(
    ((end.getTime() - start.getTime()) / 3_600_000) * HOUR_PX - 2,
    18,
  )
  return (
    <button
      onClick={onOpen}
      title={`${formatTime(appointment.startAt)} ${appointment.patientName} — ${appointment.reason ?? ''}`}
      className={`absolute right-0.5 left-0.5 overflow-hidden rounded border px-1 py-0.5 text-left text-[10.5px] leading-tight font-semibold transition-opacity hover:opacity-80 ${blockTones[appointment.status]}`}
      style={{ top, height }}
    >
      {formatTime(appointment.startAt)} {appointment.patientName}
    </button>
  )
}

export function WeekView({ onOpenAppointment }: { onOpenAppointment: (a: Appointment) => void }) {
  const { data: clinicians } = useCliniciansQuery()
  const [clinicianId, setClinicianId] = useState('')
  const [weekStart, setWeekStart] = useState(() => mondayOf(todayIso()))
  const effectiveClinician = clinicianId || clinicians?.[0]?.id || ''
  const { data, isLoading, isFetching } = useWeekAppointmentsQuery(
    { start: weekStart, clinicianId: effectiveClinician || undefined },
    { skip: !effectiveClinician },
  )

  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i))
  const hours = Array.from({ length: CLOSE_HOUR - OPEN_HOUR }, (_, i) => OPEN_HOUR + i)
  const today = todayIso()

  return (
    <Card flush className={isFetching ? 'opacity-60' : ''}>
      <div className="border-line flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3">
        <div className="flex items-center gap-1.5">
          <Button variant="secondary" size="sm" onClick={() => setWeekStart(addDays(weekStart, -7))} aria-label="Previous week">
            <i className="iconify tabler--chevron-left" aria-hidden />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setWeekStart(mondayOf(todayIso()))}>
            This week
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setWeekStart(addDays(weekStart, 7))} aria-label="Next week">
            <i className="iconify tabler--chevron-right" aria-hidden />
          </Button>
          <span className="text-ink ml-2 text-[13px] font-semibold">
            {new Date(`${weekStart}T00:00:00`).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
          </span>
        </div>
        <div className="w-52">
          <Select value={effectiveClinician} onChange={(e) => setClinicianId(e.target.value)} aria-label="Clinician">
            {clinicians?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.displayName}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {isLoading && <Spinner />}
      {data && (
        <div className="overflow-x-auto">
          <div className="min-w-175">
            {/* Day headers */}
            <div className="border-line grid grid-cols-[48px_repeat(7,1fr)] border-b">
              <div />
              {days.map((day) => {
                const d = new Date(`${day}T00:00:00`)
                return (
                  <div
                    key={day}
                    className={`border-line border-l px-2 py-1.5 text-center text-[11px] font-bold ${
                      day === today ? 'text-primary' : 'text-ink-muted'
                    }`}
                  >
                    {d.toLocaleDateString('en-US', { weekday: 'short' })}{' '}
                    <span className="tabular-nums">{d.getDate()}</span>
                  </div>
                )
              })}
            </div>
            {/* Grid body */}
            <div className="grid grid-cols-[48px_repeat(7,1fr)]">
              <div className="relative" style={{ height: hours.length * HOUR_PX }}>
                {hours.map((hour, i) => (
                  <span
                    key={hour}
                    className="text-ink-faint absolute right-1.5 -translate-y-1/2 text-[10px] tabular-nums"
                    style={{ top: i * HOUR_PX }}
                  >
                    {hour}:00
                  </span>
                ))}
              </div>
              {days.map((day) => (
                <div
                  key={day}
                  className={`border-line relative border-l ${day === today ? 'bg-primary/3' : ''}`}
                  style={{ height: hours.length * HOUR_PX }}
                >
                  {hours.map((hour, i) => (
                    <div
                      key={hour}
                      className="border-line/60 absolute right-0 left-0 border-t"
                      style={{ top: i * HOUR_PX }}
                    />
                  ))}
                  {data
                    .filter((a) => a.startAt.slice(0, 10) === day)
                    .map((a) => (
                      <Block key={a.id} appointment={a} onOpen={() => onOpenAppointment(a)} />
                    ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}
