import { baseApi } from '../../shared/api/baseApi'
import type { Page } from '../../shared/api/types'
import type { Dashboard, RiskFlag } from './types'

export const dashboardApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    dashboard: build.query<Dashboard, void>({
      query: () => '/dashboard',
      providesTags: ['Dashboard'],
    }),
    riskFlags: build.query<Page<RiskFlag>, { limit?: number; offset?: number }>({
      query: (params) => ({ url: '/dashboard/risk-flags', params }),
      providesTags: ['Dashboard'],
    }),
  }),
})

export const { useDashboardQuery, useRiskFlagsQuery } = dashboardApi
