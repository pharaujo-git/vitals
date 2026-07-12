import { baseApi } from '../../shared/api/baseApi'
import type { Page } from '../../shared/api/types'

export interface TimelineEvent {
  kind: 'encounter' | 'appointment' | 'problem' | 'medication' | 'allergy'
  at: string
  title: string
  detail: string | null
  source: string | null
}

export const timelineApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    timeline: build.query<
      Page<TimelineEvent>,
      { patientId: string; limit?: number; offset?: number }
    >({
      query: ({ patientId, ...params }) => ({ url: `/patients/${patientId}/timeline`, params }),
      providesTags: ['Timeline', 'Encounter', 'Appointment', 'ClinicalList'],
    }),
  }),
})

export const { useTimelineQuery } = timelineApi
