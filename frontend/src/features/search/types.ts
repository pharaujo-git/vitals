export interface PatientHit {
  id: string
  mrn: string
  firstName: string
  lastName: string
  dob: string
}

export interface EncounterHit {
  id: string
  patientId: string
  patientName: string
  reason: string | null
  occurredAt: string
}

export interface SearchResults {
  patients: PatientHit[]
  encounters: EncounterHit[]
}
