export interface Observation {
  id: string
  code: string
  valueNum: number | null
  valueText: string | null
  unit: string | null
  takenAt: string
  source: string
}

export interface ObservationInput {
  code: string
  valueNum: number | null
  valueText: string | null
  takenAt?: string | null
}

export interface Encounter {
  id: string
  patientId: string
  clinicianName: string | null
  occurredAt: string
  encounterType: string
  reason: string | null
  notes: string | null
  source: string
  observations: Observation[]
}

export interface EncounterInput {
  occurredAt: string
  encounterType: string
  reason: string | null
  notes: string | null
  observations: ObservationInput[]
}

export interface ObservationType {
  code: string
  label: string
  kind: 'numeric' | 'text'
  unit: string | null
  minValue: number | null
  maxValue: number | null
}

export const encounterTypeLabels: Record<string, string> = {
  visit: 'Office visit',
  admission: 'Admission',
  telehealth: 'Telehealth',
  imported: 'Imported',
}

export function formatObservationValue(o: Observation): string {
  if (o.valueNum !== null) return `${o.valueNum}${o.unit ? ` ${o.unit}` : ''}`
  return o.valueText ?? '—'
}
