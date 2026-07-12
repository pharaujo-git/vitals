import { baseApi } from '../../shared/api/baseApi'
import type { Page } from '../../shared/api/types'
import type { Consent, Patient, PatientFilters, PatientInput } from './types'

export const patientsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    patients: build.query<Page<Patient>, PatientFilters>({
      query: (filters) => ({ url: '/patients', params: { ...filters } }),
      providesTags: ['Patient'],
    }),
    patient: build.query<Patient, string>({
      query: (id) => `/patients/${id}`,
      providesTags: (_r, _e, id) => [{ type: 'Patient', id }],
    }),
    createPatient: build.mutation<Patient, PatientInput>({
      query: (body) => ({ url: '/patients', method: 'POST', body }),
      invalidatesTags: ['Patient', 'Dashboard'],
    }),
    updatePatient: build.mutation<Patient, { id: string } & PatientInput>({
      query: ({ id, ...body }) => ({ url: `/patients/${id}`, method: 'PUT', body }),
      invalidatesTags: (_r, _e, { id }) => ['Patient', 'Dashboard', { type: 'Patient', id }],
    }),
    consent: build.query<Consent, string>({
      query: (id) => `/patients/${id}/consent`,
      providesTags: ['Consent'],
    }),
    updateConsent: build.mutation<
      Consent,
      { id: string; restricted: boolean; grants: { granteeType: string; grantee: string }[] }
    >({
      query: ({ id, ...body }) => ({ url: `/patients/${id}/consent`, method: 'PUT', body }),
      invalidatesTags: (_r, _e, { id }) => ['Consent', 'Patient', { type: 'Patient', id }],
    }),
  }),
})

export const {
  usePatientsQuery,
  usePatientQuery,
  useCreatePatientMutation,
  useUpdatePatientMutation,
  useConsentQuery,
  useUpdateConsentMutation,
} = patientsApi
