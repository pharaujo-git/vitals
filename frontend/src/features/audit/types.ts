export interface AuditEntry {
  id: string
  userEmail: string
  action: string
  entityType: string | null
  entityId: string | null
  detail: Record<string, unknown> | null
  createdAt: string
}

export interface AuditFilters {
  action?: string
  entityId?: string
  limit?: number
  offset?: number
}
