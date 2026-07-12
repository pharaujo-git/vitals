export interface DuplicatePatient {
  id: string
  mrn: string
  firstName: string
  lastName: string
  dob: string
  sex: string
  source: string
}

export interface DuplicateFlag {
  id: string
  patientA: DuplicatePatient
  patientB: DuplicatePatient
  reason: string
  status: 'pending' | 'merged' | 'dismissed'
  createdAt: string
  resolvedAt: string | null
}

export interface SourceContribution {
  source: string
  encounters: number
  observations: number
}

export interface PatientSummary {
  sources: SourceContribution[]
  latestObservations: {
    id: string
    code: string
    valueNum: number | null
    valueText: string | null
    unit: string | null
    takenAt: string
    source: string
  }[]
  pendingDuplicates: number
}
