import { baseApi } from '../../shared/api/baseApi'

export interface TrendSeries {
  code: string
  label: string
  unit: string | null
  points: { takenAt: string; value: number }[]
}

export const trendsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    observationTrends: build.query<TrendSeries[], string>({
      query: (patientId) => `/patients/${patientId}/observations/trends`,
      providesTags: ['Observation', 'Encounter'],
    }),
  }),
})

export const { useObservationTrendsQuery } = trendsApi
