import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { AttachmentsCard } from '../attachments/AttachmentsCard'
import { ClinicalListsCard } from '../clinical/ClinicalListsCard'
import { TimelineCard } from '../timeline/TimelineCard'
import { TrendsCard } from '../trends/TrendsCard'
import { ConsolidatedCard } from '../duplicates/ConsolidatedCard'
import { EncountersCard } from '../encounters/EncountersCard'
import { useLazyExportFhirQuery } from '../fhir/api'
import { useHasRole } from '../../shared/hooks/useRole'
import { ageFromDob, formatDate } from '../../shared/lib/format'
import { Badge } from '../../shared/ui/Badge'
import { Button } from '../../shared/ui/Button'
import { Card, EmptyState, ErrorNote, PageBody, PageHeader, Spinner } from '../../shared/ui/Page'
import { usePatientQuery } from './api'
import { ConsentCard } from './ConsentCard'
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
  const isAdmin = useHasRole()
  const [exportFhir, { isFetching: exporting }] = useLazyExportFhirQuery()

  async function onExportFhir() {
    if (!patient) return
    const result = await exportFhir(patient.id)
    if (!result.data) return
    const blob = new Blob([JSON.stringify(result.data, null, 2)], { type: 'application/fhir+json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${patient.mrn}-fhir-bundle.json`
    a.click()
    URL.revokeObjectURL(url)
  }

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
            {patient.restricted && (
              <Badge tone="red">
                <i className="iconify tabler--lock size-3" aria-hidden /> Restricted
              </Badge>
            )}
            <SourceBadge source={patient.source} />
            {canEdit && (
              <Button size="sm" variant="secondary" onClick={onExportFhir} disabled={exporting}>
                <i className="iconify tabler--file-export" aria-hidden />
                {exporting ? 'Exporting…' : 'Export FHIR'}
              </Button>
            )}
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
          <div className="mt-4 grid items-start gap-4 lg:grid-cols-2">
            <EncountersCard patientId={patient.id} canEdit={canEdit} />
            <div className="space-y-4">
              <ClinicalListsCard patientId={patient.id} />
              <ConsolidatedCard patientId={patient.id} />
            </div>
          </div>
        )}

        {canEdit && (
          <div className="mt-4 space-y-4">
            <TrendsCard patientId={patient.id} />
            <div className="grid items-start gap-4 lg:grid-cols-2">
              <AttachmentsCard patientId={patient.id} />
              <TimelineCard patientId={patient.id} />
            </div>
          </div>
        )}

        {isAdmin && (
          <div className="mt-4">
            <ConsentCard patientId={patient.id} />
          </div>
        )}

        {editing && <PatientModal patient={patient} onClose={() => setEditing(false)} />}
      </PageBody>
    </>
  )
}
