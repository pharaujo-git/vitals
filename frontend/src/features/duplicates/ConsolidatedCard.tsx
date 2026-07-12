import { Link } from 'react-router-dom'
import { formatDateTime } from '../../shared/lib/format'
import { Card, Spinner } from '../../shared/ui/Page'
import { SourceBadge } from '../patients/PatientsPage'
import { usePatientSummaryQuery } from './api'

const codeLabels: Record<string, string> = {
  heart_rate: 'Heart rate',
  bp_systolic: 'Systolic BP',
  bp_diastolic: 'Diastolic BP',
  temperature: 'Temperature',
  resp_rate: 'Respiratory rate',
  spo2: 'SpO₂',
  weight: 'Weight',
  height: 'Height',
  bmi: 'BMI',
  glucose: 'Glucose',
  hba1c: 'HbA1c',
  note: 'Note',
}

/** Consolidated view across sources: contributions + latest value per observation. */
export function ConsolidatedCard({ patientId }: { patientId: string }) {
  const { data, isLoading } = usePatientSummaryQuery(patientId)

  return (
    <Card title="Consolidated record">
      {isLoading && <Spinner />}
      {data && (
        <div className="space-y-4">
          {data.pendingDuplicates > 0 && (
            <Link
              to="/duplicates"
              className="bg-accent-amber/15 text-accent-amber flex items-center gap-2 rounded-md p-3 text-[13px] font-semibold hover:underline"
            >
              <i className="iconify tabler--alert-triangle size-4.5 shrink-0" aria-hidden />
              {data.pendingDuplicates} possible duplicate record
              {data.pendingDuplicates === 1 ? '' : 's'} flagged for review
            </Link>
          )}

          <div>
            <p className="text-ink-muted mb-2 text-xs font-semibold">Contributing sources</p>
            <div className="flex flex-wrap gap-2">
              {data.sources.map((s) => (
                <div key={s.source} className="border-line flex items-center gap-2 rounded-md border px-2.5 py-1.5">
                  <SourceBadge source={s.source} />
                  <span className="text-ink-muted text-xs">
                    {s.encounters} enc · {s.observations} obs
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <p className="text-ink-muted mb-2 text-xs font-semibold">
              Latest observations (all sources)
            </p>
            {data.latestObservations.length === 0 && (
              <p className="text-ink-faint text-xs">No observations recorded yet.</p>
            )}
            {data.latestObservations.length > 0 && (
              <table className="w-full text-[12.5px]">
                <tbody className="divide-line divide-y">
                  {data.latestObservations
                    .filter((o) => o.code !== 'note')
                    .map((o) => (
                      <tr key={o.id}>
                        <td className="text-ink-muted py-1.5 pr-3">{codeLabels[o.code] ?? o.code}</td>
                        <td className="text-ink py-1.5 pr-3 font-semibold whitespace-nowrap">
                          {o.valueNum !== null ? `${o.valueNum} ${o.unit ?? ''}` : o.valueText}
                        </td>
                        <td className="py-1.5 pr-3">
                          <SourceBadge source={o.source} />
                        </td>
                        <td className="text-ink-faint py-1.5 text-right text-[11px] whitespace-nowrap">
                          {formatDateTime(o.takenAt)}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </Card>
  )
}
