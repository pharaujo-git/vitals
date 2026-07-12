import { baseApi } from '../../shared/api/baseApi'

export interface Attachment {
  id: string
  kind: 'imaging' | 'document'
  filename: string
  contentType: string
  description: string | null
  size: number
  uploadedByName: string | null
  createdAt: string
}

export const attachmentsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    attachments: build.query<Attachment[], string>({
      query: (patientId) => `/patients/${patientId}/attachments`,
      providesTags: ['Attachment'],
    }),
    uploadAttachment: build.mutation<
      Attachment,
      { patientId: string; file: File; kind: string; description: string | null }
    >({
      query: ({ patientId, file, kind, description }) => {
        const body = new FormData()
        body.append('file', file)
        body.append('kind', kind)
        if (description) body.append('description', description)
        return { url: `/patients/${patientId}/attachments`, method: 'POST', body }
      },
      invalidatesTags: ['Attachment'],
    }),
    deleteAttachment: build.mutation<void, string>({
      query: (id) => ({ url: `/attachments/${id}`, method: 'DELETE' }),
      invalidatesTags: ['Attachment'],
    }),
  }),
})

export const { useAttachmentsQuery, useUploadAttachmentMutation, useDeleteAttachmentMutation } =
  attachmentsApi
