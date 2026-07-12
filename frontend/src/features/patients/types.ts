export type Sex = 'female' | 'male' | 'other' | 'unknown'

export interface Patient {
  id: string
  mrn: string
  firstName: string
  lastName: string
  dob: string
  sex: Sex
  phone: string | null
  email: string | null
  address: string | null
  history: string | null
  source: string
  restricted: boolean
  createdAt: string
  updatedAt: string
  riskLevel?: 'none' | 'moderate' | 'high' | null
}

export interface ConsentGrant {
  granteeType: 'role' | 'user'
  grantee: string
  display: string
}

export interface Consent {
  restricted: boolean
  grants: ConsentGrant[]
}

export interface PatientInput {
  firstName: string
  lastName: string
  dob: string
  sex: Sex
  phone: string | null
  email: string | null
  address: string | null
  history: string | null
  mrn?: string | null
}

export interface PatientFilters {
  search?: string
  sort?: 'name' | 'dob' | 'newest'
  limit?: number
  offset?: number
}

export const sourceLabels: Record<string, string> = {
  manual: 'Manual',
  csv: 'CSV import',
  hl7: 'HL7 feed',
  fhir: 'FHIR import',
}

export function patientName(p: { firstName: string; lastName: string }): string {
  return `${p.firstName} ${p.lastName}`
}
