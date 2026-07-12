import { baseApi } from '../../shared/api/baseApi'
import type { SearchResults } from './types'

export const searchApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    globalSearch: build.query<SearchResults, string>({
      query: (q) => ({ url: '/search', params: { q } }),
    }),
  }),
})

export const { useGlobalSearchQuery } = searchApi
