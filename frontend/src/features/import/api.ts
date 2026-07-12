import { baseApi } from '../../shared/api/baseApi'
import type { Page } from '../../shared/api/types'
import type { ImportBatch, ImportIssue, ImportTextInput } from './types'

export const importApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    importBatches: build.query<Page<ImportBatch>, { limit?: number; offset?: number }>({
      query: (params) => ({ url: '/imports', params }),
      providesTags: ['Import'],
    }),
    importIssues: build.query<
      Page<ImportIssue>,
      { batchId: string; limit?: number; offset?: number }
    >({
      query: ({ batchId, ...params }) => ({ url: `/imports/${batchId}/issues`, params }),
      providesTags: ['Import'],
    }),
    importCsv: build.mutation<ImportBatch, ImportTextInput>({
      query: (body) => ({ url: '/imports/csv', method: 'POST', body }),
      invalidatesTags: ['Import', 'Patient', 'Encounter', 'Observation', 'Dashboard', 'Duplicate'],
    }),
    importHl7: build.mutation<ImportBatch, ImportTextInput>({
      query: (body) => ({ url: '/imports/hl7', method: 'POST', body }),
      invalidatesTags: ['Import', 'Patient', 'Encounter', 'Observation', 'Dashboard', 'Duplicate'],
    }),
  }),
})

export const {
  useImportBatchesQuery,
  useImportIssuesQuery,
  useImportCsvMutation,
  useImportHl7Mutation,
} = importApi
