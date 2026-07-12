import { baseApi } from '../../shared/api/baseApi'
import type { Page } from '../../shared/api/types'
import type { Appointment, AppointmentFilters, AppointmentInput, Clinician } from './types'

export const appointmentsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    appointments: build.query<Page<Appointment>, AppointmentFilters>({
      query: (filters) => ({ url: '/appointments', params: { ...filters } }),
      providesTags: ['Appointment'],
    }),
    clinicians: build.query<Clinician[], void>({
      query: () => '/appointments/clinicians',
    }),
    weekAppointments: build.query<Appointment[], { start: string; clinicianId?: string }>({
      query: (params) => ({ url: '/appointments/week', params }),
      providesTags: ['Appointment'],
    }),
    nextFreeSlot: build.query<
      { startAt: string; endAt: string },
      { clinicianId: string; duration: number; day?: string }
    >({
      query: (params) => ({ url: '/appointments/next-free', params }),
    }),
    bookAppointment: build.mutation<Appointment, AppointmentInput>({
      query: (body) => ({ url: '/appointments', method: 'POST', body }),
      invalidatesTags: ['Appointment', 'Dashboard'],
    }),
    rescheduleAppointment: build.mutation<Appointment, { id: string } & AppointmentInput>({
      query: ({ id, ...body }) => ({ url: `/appointments/${id}`, method: 'PUT', body }),
      invalidatesTags: ['Appointment', 'Dashboard'],
    }),
    setAppointmentStatus: build.mutation<Appointment, { id: string; status: string }>({
      query: ({ id, status }) => ({
        url: `/appointments/${id}/status`,
        method: 'POST',
        body: { status },
      }),
      invalidatesTags: ['Appointment', 'Dashboard'],
    }),
  }),
})

export const {
  useAppointmentsQuery,
  useCliniciansQuery,
  useWeekAppointmentsQuery,
  useLazyNextFreeSlotQuery,
  useBookAppointmentMutation,
  useRescheduleAppointmentMutation,
  useSetAppointmentStatusMutation,
} = appointmentsApi
