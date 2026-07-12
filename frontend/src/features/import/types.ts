export interface ImportBatch {
  id: string
  label: string
  format: string
  totalRecords: number
  importedCount: number
  errorCount: number
  createdAt: string
}

export interface ImportIssue {
  id: string
  recordNumber: number
  message: string
  raw: string | null
}

export interface ImportTextInput {
  label: string
  content: string
}
