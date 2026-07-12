import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { EncountersCard } from '../encounters/EncountersCard'
import { useHasRole } from '../../shared/hooks/useRole'
import { ageFromDob, formatDate } from '../../shared/lib/format'
import { Button } from '../../shared/ui/Button'
import { Card, EmptyState, ErrorNote, PageBody, PageHeader, Spinner } from '../../shared/ui/Page'
import { usePatientQuery } from './api'
import { PatientModal } from './PatientModal'
import { SourceBadge } from './PatientsPage'
import { patientName, type Patient } from './types'

function DemographicsCard({ patient }: { patient: Patient }) {
  const rows: [string, string][] = [
    ['Identifier', patient.mrn],
    ['Date of birth', `${formatDate(patient.dob)} (${ageFromDob(patient.dob)} years)`],
    ['Sex', patient.sex],
    ['Phone', patient.phone ?? '—'],
    ['Email', patient.email ?? '—'],
    ['Address', patient.address ?? '—'],
  ]
  return (
    <Card title="Demographics" flush>
      <dl className="divide-line divide-y">
        {rows.map(([label, value]) => (
          <div key={label} className="flex items-baseline gap-4 px-5 py-2.5">
            <dt className="text-ink-muted w-28 shrink-0 text-xs font-semibold">{label}</dt>
            <dd className="text-ink text-[13px] capitalize">{value}</dd>
          </div>
        ))}
      </dl>
    </Card>
  )
}

export function PatientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: patient, isLoading, error } = usePatientQuery(id!)
  const [editing, setEditing] = useState(false)
  const canEdit = useHasRole('clinician')

  if (isLoading) return <Spinner />
  if (error !== undefined || !patient) {
    return (
      <PageBody>
        <ErrorNote error={error ?? { data: { detail: 'Patient not found' } }} />
      </PageBody>
    )
  }

  return (
    <>
      <PageHeader
        title={patientName(patient)}
        actions={
          <div className="flex items-center gap-2">
            <SourceBadge source={patient.source} />
            {canEdit && (
              <Button size="sm" variant="secondary" onClick={() => setEditing(true)}>
                <i className="iconify tabler--pencil" aria-hidden /> Edit
              </Button>
            )}
          </div>
        }
      />
      <PageBody>
        <p className="text-ink-muted mb-4 text-xs">
          <Link to="/patients" className="text-primary hover:underline">
            Patients
          </Link>{' '}
          / {patient.mrn}
        </p>
        <div className="grid gap-4 lg:grid-cols-2">
          <DemographicsCard patient={patient} />
          <Card title="Medical history">
            {patient.history ? (
              <p className="text-ink text-[13px] whitespace-pre-wrap">{patient.history}</p>
            ) : (
              <EmptyState icon="tabler--notes-off" message="No history recorded." />
            )}
          </Card>
        </div>

        {canEdit && (
          <div className="mt-4">
            <EncountersCard patientId={patient.id} canEdit={canEdit} />
          </div>
        )}

        {editing && <PatientModal patient={patient} onClose={() => setEditing(false)} />}
      </PageBody>
    </>
  )
}
