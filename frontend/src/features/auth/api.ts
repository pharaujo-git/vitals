import { baseApi } from '../../shared/api/baseApi'
import type { AuthResponse, User } from '../../shared/api/types'

export const authApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    login: build.mutation<AuthResponse, { email: string; password: string }>({
      query: (body) => ({ url: '/auth/login', method: 'POST', body }),
    }),
    register: build.mutation<
      AuthResponse,
      { email: string; password: string; displayName: string; role: string }
    >({
      query: (body) => ({ url: '/auth/register', method: 'POST', body }),
    }),
    me: build.query<User, void>({
      query: () => '/auth/me',
    }),
    logout: build.mutation<void, void>({
      query: () => ({ url: '/auth/logout', method: 'POST' }),
    }),
  }),
})

export const { useLoginMutation, useRegisterMutation, useMeQuery, useLogoutMutation } = authApi
