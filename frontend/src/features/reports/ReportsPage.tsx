import { useState } from 'react'
import { usePagination } from '../../shared/hooks/usePagination'
import { todayIso } from '../../shared/lib/format'
import { Badge } from '../../shared/ui/Badge'
import { Button } from '../../shared/ui/Button'
import { Input, Select } from '../../shared/ui/Field'
import { Card, EmptyState, PageBody, PageHeader, Spinner } from '../../shared/ui/Page'
import { Pagination } from '../../shared/ui/Pagination'
import { SourceBadge } from '../patients/PatientsPage'
import { useCohortQuery, useLazyExportCohortQuery } from './api'

const riskTones: Record<string, 'red' | 'amber' | 'muted'> = {
  high: 'red',
  moderate: 'amber',
  none: 'muted',
}

export function ReportsPage() {
  const [minAge, setMinAge] = useState('')
  const [maxAge, setMaxAge] = useState('')
  const [sex, setSex] = useState('')
  const [source, setSource] = useState('')
  const [riskLevel, setRiskLevel] = useState('')
  const { limit, offset, setPage, reset } = usePagination()

  const filters = {
    minAge: minAge ? Number(minAge) : undefined,
    maxAge: maxAge ? Number(maxAge) : undefined,
    sex: sex || undefined,
    source: source || undefined,
    riskLevel: riskLevel || undefined,
  }
  const { data, isLoading, isFetching } = useCohortQuery({ ...filters, limit, offset })
  const [exportCohort, { isFetching: exporting }] = useLazyExportCohortQuery()

  const identified = data?.columns.includes('mrn') ?? false

  async function onExport() {
    const result = await exportCohort(filters)
    if (result.data === undefined) return
    const blob = new Blob([result.data], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `vitals-cohort-${todayIso()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <>
      <PageHeader
        title="Cohort reports"
        actions={
          <Button size="sm" onClick={onExport} disabled={exporting || !data || data.total === 0}>
            <i className="iconify tabler--download" aria-hidden />
            {exporting ? 'Exporting…' : 'Export CSV'}
          </Button>
        }
      />
      <PageBody>
        <Card className="mb-4">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <Input
              label="Min age"
              type="number"
              min={0}
              max={150}
              placeholder="0"
              value={minAge}
              onChange={(e) => {
                setMinAge(e.target.value)
                reset()
              }}
            />
            <Input
              label="Max age"
              type="number"
              min={0}
              max={150}
              placeholder="120"
              value={maxAge}
              onChange={(e) => {
                setMaxAge(e.target.value)
                reset()
              }}
            />
            <Select
              label="Sex"
              value={sex}
              onChange={(e) => {
                setSex(e.target.value)
                reset()
              }}
            >
              <option value="">Any</option>
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="other">Other</option>
              <option value="unknown">Unknown</option>
            </Select>
            <Select
              label="Source"
              value={source}
              onChange={(e) => {
                setSource(e.target.value)
                reset()
              }}
            >
              <option value="">Any</option>
              <option value="manual">Manual</option>
              <option value="csv">CSV import</option>
              <option value="hl7">HL7 feed</option>
              <option value="fhir">FHIR import</option>
            </Select>
            <Select
              label="Risk"
              value={riskLevel}
              onChange={(e) => {
                setRiskLevel(e.target.value)
                reset()
              }}
            >
              <option value="">Any</option>
              <option value="flagged">Flagged (any level)</option>
              <option value="high">High</option>
              <option value="moderate">Moderate</option>
            </Select>
          </div>
          <p className="text-ink-muted mt-3 text-xs">
            {identified ? (
              <>
                <i className="iconify tabler--id mr-1 align-[-2px]" aria-hidden />
                Identified export: includes name, MRN, date of birth and contact fields.
              </>
            ) : (
              <>
                <i className="iconify tabler--eye-off mr-1 align-[-2px]" aria-hidden />
                De-identified export: name, MRN, date of birth and contact fields are excluded for
                your role.
              </>
            )}
          </p>
        </Card>

        {isLoading && <Spinner />}
        {data && data.items.length === 0 && (
          <EmptyState icon="tabler--report-off" message="No patients match this cohort." />
        )}
        {data && data.items.length > 0 && (
          <Card flush className={isFetching ? 'opacity-60' : ''}>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="bg-well text-ink-muted border-line border-b text-left text-[10.5px] font-bold tracking-[0.08em] uppercase">
                    {identified && <th className="px-5 py-2.5">Patient</th>}
                    <th className="px-5 py-2.5">Age</th>
                    <th className="px-5 py-2.5">Sex</th>
                    <th className="px-5 py-2.5">Source</th>
                    <th className="px-5 py-2.5 text-right">Encounters</th>
                    <th className="px-5 py-2.5">Risk</th>
                  </tr>
                </thead>
                <tbody className="divide-line divide-y">
                  {data.items.map((row) => (
                    <tr key={row.patientId} className="hover:bg-well/60 transition-colors">
                      {identified && (
                        <td className="px-5 py-2.5">
                          <span className="text-ink font-medium">
                            {row.lastName}, {row.firstName}
                          </span>
                          <span className="text-ink-muted block font-mono text-xs">{row.mrn}</span>
                        </td>
                      )}
                      <td className="text-ink-muted px-5 py-2.5">{row.age}</td>
                      <td className="text-ink-muted px-5 py-2.5 capitalize">{row.sex}</td>
                      <td className="px-5 py-2.5">
                        <SourceBadge source={row.source} />
                      </td>
                      <td className="text-ink-muted px-5 py-2.5 text-right tabular-nums">
                        {row.encounters}
                      </td>
                      <td className="px-5 py-2.5">
                        <Badge tone={riskTones[row.riskLevel] ?? 'muted'}>
                          {row.riskLevel === 'none' ? 'none' : `${row.riskLevel} · ${row.riskScore}`}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination total={data.total} limit={limit} offset={offset} onPage={setPage} noun="patient" />
          </Card>
        )}
      </PageBody>
    </>
  )
}
