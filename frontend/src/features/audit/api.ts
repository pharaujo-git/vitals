import { baseApi } from '../../shared/api/baseApi'
import type { Page } from '../../shared/api/types'
import type { AuditEntry, AuditFilters } from './types'

export const auditApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    auditEntries: build.query<Page<AuditEntry>, AuditFilters>({
      query: (filters) => ({ url: '/audit', params: { ...filters } }),
      providesTags: ['Audit'],
    }),
    auditActions: build.query<string[], void>({
      query: () => '/audit/actions',
      providesTags: ['Audit'],
    }),
  }),
})

export const { useAuditEntriesQuery, useAuditActionsQuery } = auditApi
