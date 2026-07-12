export type AppointmentStatus = 'booked' | 'cancelled' | 'completed'

export interface Appointment {
  id: string
  patientId: string
  patientName: string
  patientMrn: string
  clinicianId: string
  clinicianName: string
  startAt: string
  endAt: string
  reason: string | null
  status: AppointmentStatus
}

export interface AppointmentInput {
  patientId: string
  clinicianId: string
  startAt: string
  endAt: string
  reason: string | null
}

export interface Clinician {
  id: string
  displayName: string
}

export interface AppointmentFilters {
  day?: string
  clinicianId?: string
  patientId?: string
  status?: string
  limit?: number
  offset?: number
}
