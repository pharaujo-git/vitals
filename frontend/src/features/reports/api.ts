import { baseApi } from '../../shared/api/baseApi'
import type { CohortFilters, CohortPreview } from './types'

export const reportsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    cohort: build.query<CohortPreview, CohortFilters>({
      query: (filters) => ({ url: '/reports/cohort', params: { ...filters } }),
      providesTags: ['Report'],
    }),
    exportCohort: build.query<string, CohortFilters>({
      query: (filters) => ({
        url: '/reports/cohort/export',
        params: { ...filters },
        responseHandler: (response) => response.text(),
      }),
    }),
  }),
})

export const { useCohortQuery, useLazyExportCohortQuery } = reportsApi
