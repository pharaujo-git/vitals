import { baseApi } from '../../shared/api/baseApi'
import type { ImportBatch, ImportTextInput } from '../import/types'

export const fhirApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    exportFhir: build.query<Record<string, unknown>, string>({
      query: (patientId) => `/patients/${patientId}/fhir`,
    }),
    importFhir: build.mutation<ImportBatch, ImportTextInput>({
      query: (body) => ({ url: '/fhir/import', method: 'POST', body }),
      invalidatesTags: ['Import', 'Patient', 'Encounter', 'Observation', 'Dashboard', 'Duplicate'],
    }),
  }),
})

export const { useLazyExportFhirQuery, useImportFhirMutation } = fhirApi
