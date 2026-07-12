import { baseApi } from '../../shared/api/baseApi'
import type { Allergy, ClinicalLists, Medication, Problem } from './types'

export const clinicalApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    clinicalLists: build.query<ClinicalLists, string>({
      query: (patientId) => `/patients/${patientId}/clinical-lists`,
      providesTags: ['ClinicalList'],
    }),
    addProblem: build.mutation<
      Problem,
      { patientId: string; description: string; icdCode: string | null; status: string; onsetDate: string | null }
    >({
      query: ({ patientId, ...body }) => ({
        url: `/patients/${patientId}/problems`,
        method: 'POST',
        body,
      }),
      invalidatesTags: ['ClinicalList', 'Dashboard', 'Timeline'],
    }),
    updateProblem: build.mutation<
      Problem,
      { id: string; description: string; icdCode: string | null; status: string; onsetDate: string | null }
    >({
      query: ({ id, ...body }) => ({ url: `/problems/${id}`, method: 'PUT', body }),
      invalidatesTags: ['ClinicalList', 'Dashboard', 'Timeline'],
    }),
    deleteProblem: build.mutation<void, string>({
      query: (id) => ({ url: `/problems/${id}`, method: 'DELETE' }),
      invalidatesTags: ['ClinicalList', 'Dashboard', 'Timeline'],
    }),
    addMedication: build.mutation<
      Medication,
      { patientId: string; name: string; dose: string | null; frequency: string | null; active: boolean; startedDate: string | null }
    >({
      query: ({ patientId, ...body }) => ({
        url: `/patients/${patientId}/medications`,
        method: 'POST',
        body,
      }),
      invalidatesTags: ['ClinicalList', 'Dashboard', 'Timeline'],
    }),
    updateMedication: build.mutation<
      Medication,
      { id: string; name: string; dose: string | null; frequency: string | null; active: boolean; startedDate: string | null }
    >({
      query: ({ id, ...body }) => ({ url: `/medications/${id}`, method: 'PUT', body }),
      invalidatesTags: ['ClinicalList', 'Dashboard', 'Timeline'],
    }),
    deleteMedication: build.mutation<void, string>({
      query: (id) => ({ url: `/medications/${id}`, method: 'DELETE' }),
      invalidatesTags: ['ClinicalList', 'Dashboard', 'Timeline'],
    }),
    addAllergy: build.mutation<
      Allergy,
      { patientId: string; substance: string; reaction: string | null; severity: string }
    >({
      query: ({ patientId, ...body }) => ({
        url: `/patients/${patientId}/allergies`,
        method: 'POST',
        body,
      }),
      invalidatesTags: ['ClinicalList', 'Timeline'],
    }),
    deleteAllergy: build.mutation<void, string>({
      query: (id) => ({ url: `/allergies/${id}`, method: 'DELETE' }),
      invalidatesTags: ['ClinicalList', 'Timeline'],
    }),
  }),
})

export const {
  useClinicalListsQuery,
  useAddProblemMutation,
  useUpdateProblemMutation,
  useDeleteProblemMutation,
  useAddMedicationMutation,
  useUpdateMedicationMutation,
  useDeleteMedicationMutation,
  useAddAllergyMutation,
  useDeleteAllergyMutation,
} = clinicalApi
