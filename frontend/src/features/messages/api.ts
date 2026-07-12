import { baseApi } from '../../shared/api/baseApi'
import type { Page } from '../../shared/api/types'
import type { Message, MessageInput, Recipient } from './types'

export const messagesApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    inbox: build.query<Page<Message>, { unread?: boolean; limit?: number; offset?: number }>({
      query: (params) => ({ url: '/messages/inbox', params }),
      providesTags: ['Message'],
    }),
    sentMessages: build.query<Page<Message>, { limit?: number; offset?: number }>({
      query: (params) => ({ url: '/messages/sent', params }),
      providesTags: ['Message'],
    }),
    unreadCount: build.query<{ count: number }, void>({
      query: () => '/messages/unread-count',
      providesTags: ['Message'],
    }),
    recipients: build.query<Recipient[], void>({
      query: () => '/messages/recipients',
    }),
    sendMessage: build.mutation<Message, MessageInput>({
      query: (body) => ({ url: '/messages', method: 'POST', body }),
      invalidatesTags: ['Message'],
    }),
    // A query with side effects: opening a thread marks it read server-side,
    // so it's modeled as a mutation to invalidate inbox/unread caches.
    openThread: build.mutation<Message[], string>({
      query: (messageId) => ({ url: `/messages/${messageId}/thread`, method: 'GET' }),
      invalidatesTags: ['Message'],
    }),
  }),
})

export const {
  useInboxQuery,
  useSentMessagesQuery,
  useUnreadCountQuery,
  useRecipientsQuery,
  useSendMessageMutation,
  useOpenThreadMutation,
} = messagesApi
