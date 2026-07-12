export interface MessageAttachment {
  id: string
  filename: string
  contentType: string
  size: number
}

export interface Message {
  id: string
  rootId: string
  senderId: string
  senderName: string
  recipientId: string
  recipientName: string
  patientId: string | null
  patientName: string | null
  subject: string
  body: string
  readAt: string | null
  archivedAt: string | null
  createdAt: string
  attachments: MessageAttachment[]
}

export interface MessageInput {
  recipientIds: string[]
  subject: string
  body: string
  patientId?: string | null
  parentId?: string | null
  attachments?: { filename: string; contentType: string; dataBase64: string }[]
}

export interface Recipient {
  id: string
  displayName: string
  role: string
}
