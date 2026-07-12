import { baseApi } from '../../shared/api/baseApi'
import type { Page } from '../../shared/api/types'
import type { DuplicateFlag, PatientSummary } from './types'

export const duplicatesApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    duplicates: build.query<Page<DuplicateFlag>, { status?: string; limit?: number; offset?: number }>({
      query: (params) => ({ url: '/duplicates', params }),
      providesTags: ['Duplicate'],
    }),
    patientSummary: build.query<PatientSummary, string>({
      query: (patientId) => `/patients/${patientId}/summary`,
      providesTags: (_r, _e, id) => ['Duplicate', 'Observation', { type: 'Patient', id }],
    }),
    scanDuplicates: build.mutation<{ newFlags: number }, void>({
      query: () => ({ url: '/duplicates/scan', method: 'POST' }),
      invalidatesTags: ['Duplicate'],
    }),
    mergeDuplicate: build.mutation<DuplicateFlag, string>({
      query: (id) => ({ url: `/duplicates/${id}/merge`, method: 'POST' }),
      invalidatesTags: ['Duplicate', 'Patient', 'Encounter', 'Observation', 'Appointment', 'Dashboard'],
    }),
    dismissDuplicate: build.mutation<DuplicateFlag, string>({
      query: (id) => ({ url: `/duplicates/${id}/dismiss`, method: 'POST' }),
      invalidatesTags: ['Duplicate'],
    }),
  }),
})

export const {
  useDuplicatesQuery,
  usePatientSummaryQuery,
  useScanDuplicatesMutation,
  useMergeDuplicateMutation,
  useDismissDuplicateMutation,
} = duplicatesApi
