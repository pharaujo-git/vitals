import { baseApi } from '../../shared/api/baseApi'
import type { Page } from '../../shared/api/types'

export interface AppNotification {
  id: string
  kind: 'appointment' | 'risk' | string
  title: string
  body: string | null
  link: string | null
  readAt: string | null
  createdAt: string
}

export const notificationsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    notifications: build.query<Page<AppNotification>, { limit?: number; offset?: number }>({
      query: (params) => ({ url: '/notifications', params }),
      providesTags: ['Notification'],
    }),
    notificationUnreadCount: build.query<{ count: number }, void>({
      query: () => '/notifications/unread-count',
      providesTags: ['Notification'],
    }),
    markNotificationsRead: build.mutation<void, void>({
      query: () => ({ url: '/notifications/read-all', method: 'POST' }),
      invalidatesTags: ['Notification'],
    }),
  }),
})

export const {
  useNotificationsQuery,
  useNotificationUnreadCountQuery,
  useMarkNotificationsReadMutation,
} = notificationsApi
