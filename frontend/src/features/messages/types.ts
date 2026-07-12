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
  createdAt: string
}

export interface MessageInput {
  recipientId: string
  subject: string
  body: string
  patientId?: string | null
  parentId?: string | null
}

export interface Recipient {
  id: string
  displayName: string
  role: string
}
