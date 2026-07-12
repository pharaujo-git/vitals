import { baseApi } from '../../shared/api/baseApi'
import type { Page } from '../../shared/api/types'
import type { ManagedUser } from './types'

export const usersApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    users: build.query<Page<ManagedUser>, { search?: string; limit?: number; offset?: number }>({
      query: (params) => ({ url: '/users', params }),
      providesTags: ['User'],
    }),
    setUserRole: build.mutation<ManagedUser, { id: string; role: string }>({
      query: ({ id, role }) => ({ url: `/users/${id}/role`, method: 'POST', body: { role } }),
      invalidatesTags: ['User'],
    }),
    setUserActive: build.mutation<ManagedUser, { id: string; active: boolean }>({
      query: ({ id, active }) => ({ url: `/users/${id}/active`, method: 'POST', body: { active } }),
      invalidatesTags: ['User'],
    }),
    adminResetPassword: build.mutation<{ tempPassword: string }, string>({
      query: (id) => ({ url: `/users/${id}/reset-password`, method: 'POST' }),
    }),
  }),
})

export const {
  useUsersQuery,
  useSetUserRoleMutation,
  useSetUserActiveMutation,
  useAdminResetPasswordMutation,
} = usersApi
