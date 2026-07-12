export interface CohortRow {
  patientId: string
  mrn: string | null
  firstName: string | null
  lastName: string | null
  dob: string | null
  age: number
  sex: string
  source: string
  encounters: number
  riskScore: number
  riskLevel: string
  riskReasons: string
}

export interface CohortPreview {
  items: CohortRow[]
  total: number
  limit: number
  offset: number
  columns: string[]
}

export interface CohortFilters {
  minAge?: number
  maxAge?: number
  sex?: string
  source?: string
  riskLevel?: string
  limit?: number
  offset?: number
}
