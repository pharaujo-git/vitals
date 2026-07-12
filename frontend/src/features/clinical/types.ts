export interface Problem {
  id: string
  description: string
  icdCode: string | null
  status: 'active' | 'resolved'
  onsetDate: string | null
}

export interface Medication {
  id: string
  name: string
  dose: string | null
  frequency: string | null
  active: boolean
  startedDate: string | null
}

export interface Allergy {
  id: string
  substance: string
  reaction: string | null
  severity: 'mild' | 'moderate' | 'severe'
}

export interface ClinicalLists {
  problems: Problem[]
  medications: Medication[]
  allergies: Allergy[]
}
