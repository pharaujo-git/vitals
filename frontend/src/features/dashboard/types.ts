export interface DashboardTotals {
  patients: number
  encounters: number
  observations: number
  upcomingAppointments: number
}

export interface LabeledCount {
  label: string
  count: number
}

export interface MonthCount {
  year: number
  month: number
  count: number
}

export interface Dashboard {
  totals: DashboardTotals
  sexBreakdown: LabeledCount[]
  ageBands: LabeledCount[]
  sourceBreakdown: LabeledCount[]
  encounterTrend: MonthCount[]
  observationTrend: MonthCount[]
  riskSummary: { high: number; moderate: number; flagged: number }
}

export interface RiskFlag {
  patientId: string
  patientName: string
  mrn: string
  age: number
  score: number
  level: 'high' | 'moderate'
  reasons: string[]
}
