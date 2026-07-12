import { baseApi } from '../../shared/api/baseApi'
import type { Page } from '../../shared/api/types'
import type { Encounter, EncounterInput, ObservationInput, ObservationType } from './types'

export const encountersApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    encounters: build.query<Page<Encounter>, { patientId: string; limit?: number; offset?: number }>({
      query: ({ patientId, ...params }) => ({
        url: `/patients/${patientId}/encounters`,
        params,
      }),
      providesTags: ['Encounter'],
    }),
    observationCatalog: build.query<ObservationType[], void>({
      query: () => '/observations/catalog',
    }),
    createEncounter: build.mutation<Encounter, { patientId: string } & EncounterInput>({
      query: ({ patientId, ...body }) => ({
        url: `/patients/${patientId}/encounters`,
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Encounter', 'Observation', 'Dashboard'],
    }),
    addObservation: build.mutation<Encounter, { encounterId: string } & ObservationInput>({
      query: ({ encounterId, ...body }) => ({
        url: `/encounters/${encounterId}/observations`,
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Encounter', 'Observation', 'Dashboard'],
    }),
  }),
})

export const {
  useEncountersQuery,
  useObservationCatalogQuery,
  useCreateEncounterMutation,
  useAddObservationMutation,
} = encountersApi
