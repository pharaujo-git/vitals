import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type { BaseQueryFn, FetchArgs, FetchBaseQueryError } from '@reduxjs/toolkit/query'
import { clearCredentials, setCredentials } from '../../features/auth/authSlice'
import type { AuthResponse } from './types'

interface StateWithAuth {
  auth: { accessToken: string | null }
}

const rawBaseQuery = fetchBaseQuery({
  baseUrl: '/api',
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as StateWithAuth).auth.accessToken
    if (token) headers.set('Authorization', `Bearer ${token}`)
    return headers
  },
})

// One refresh at a time; concurrent 401s wait for the same refresh call.
let refreshPromise: Promise<AuthResponse | null> | null = null

const baseQueryWithReauth: BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError> = async (
  args,
  api,
  extraOptions,
) => {
  let result = await rawBaseQuery(args, api, extraOptions)

  if (result.error?.status === 401) {
    // The refresh token rides an httpOnly cookie; just call the endpoint.
    refreshPromise ??= Promise.resolve(
      rawBaseQuery({ url: '/auth/refresh', method: 'POST' }, api, extraOptions),
    )
      .then((r) => (r.data as AuthResponse | undefined) ?? null)
      .finally(() => {
        refreshPromise = null
      })

    const refreshed = await refreshPromise
    if (refreshed) {
      api.dispatch(setCredentials(refreshed))
      result = await rawBaseQuery(args, api, extraOptions)
    } else {
      api.dispatch(clearCredentials())
    }
  }

  return result
}

export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: [
    'Patient',
    'Appointment',
    'Encounter',
    'Observation',
    'Audit',
    'Import',
    'Duplicate',
    'Dashboard',
    'Consent',
    'Report',
    'Message',
    'ClinicalList',
    'Timeline',
    'Attachment',
  ],
  endpoints: () => ({}),
})
