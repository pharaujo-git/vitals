import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePagination } from '../../shared/hooks/usePagination'
import { useHasRole } from '../../shared/hooks/useRole'
import { ageFromDob, formatDate } from '../../shared/lib/format'
import { Badge } from '../../shared/ui/Badge'
import { Button } from '../../shared/ui/Button'
import { Input, Select } from '../../shared/ui/Field'
import { Card, EmptyState, PageBody, PageHeader, Spinner } from '../../shared/ui/Page'
import { Pagination } from '../../shared/ui/Pagination'
import { usePatientsQuery } from './api'
import { PatientModal } from './PatientModal'
import { sourceLabels, type Patient } from './types'

const sourceTones = {
  manual: 'muted',
  csv: 'blue',
  hl7: 'violet',
  fhir: 'green',
} as const

export function SourceBadge({ source }: { source: string }) {
  return (
    <Badge tone={sourceTones[source as keyof typeof sourceTones] ?? 'muted'}>
      {sourceLabels[source] ?? source}
    </Badge>
  )
}

const riskTones = { high: 'red', moderate: 'amber', none: 'muted' } as const

export function PatientsPage() {
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<'name' | 'dob' | 'newest'>('name')
  const { limit, offset, setPage, reset } = usePagination()
  const { data, isLoading, isFetching } = usePatientsQuery({
    search: search || undefined,
    sort,
    limit,
    offset,
  })
  const [editing, setEditing] = useState<Patient | 'new' | null>(null)
  const canEdit = useHasRole('clinician')
  const navigate = useNavigate()

  return (
    <>
      <PageHeader
        title="Patients"
        actions={
          canEdit ? (
            <Button size="sm" onClick={() => setEditing('new')}>
              <i className="iconify tabler--plus" aria-hidden /> New patient
            </Button>
          ) : undefined
        }
      />
      <PageBody>
        <Card className="mb-4">
          <div className="flex flex-wrap gap-3">
            <div className="min-w-52 flex-1">
              <Input
                icon="tabler--search"
                placeholder="Search by name, identifier, phone or email…"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  reset()
                }}
              />
            </div>
            <div className="w-44">
              <Select
                value={sort}
                onChange={(e) => {
                  setSort(e.target.value as typeof sort)
                  reset()
                }}
                aria-label="Sort"
              >
                <option value="name">Sort: Name</option>
                <option value="dob">Sort: Date of birth</option>
                <option value="newest">Sort: Newest first</option>
              </Select>
            </div>
          </div>
        </Card>

        {isLoading && <Spinner />}
        {data && data.items.length === 0 && (
          <EmptyState icon="tabler--users" message="No patients match. Create one to get started." />
        )}
        {data && data.items.length > 0 && (
          <Card flush className={isFetching ? 'opacity-60' : ''}>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="bg-well text-ink-muted border-line border-b text-left text-[10.5px] font-bold tracking-[0.08em] uppercase">
                    <th className="px-5 py-2.5">Patient</th>
                    <th className="px-5 py-2.5">Identifier</th>
                    <th className="px-5 py-2.5">Date of birth</th>
                    <th className="px-5 py-2.5">Sex</th>
                    <th className="px-5 py-2.5">Phone</th>
                    <th className="px-5 py-2.5">Risk</th>
                    <th className="px-5 py-2.5">Source</th>
                  </tr>
                </thead>
                <tbody className="divide-line divide-y">
                  {data.items.map((p) => (
                    <tr
                      key={p.id}
                      onClick={() => navigate(`/patients/${p.id}`)}
                      className="hover:bg-well/60 cursor-pointer transition-colors"
                    >
                      <td className="px-5 py-2.5">
                        <span className="text-ink font-medium">
                          {p.lastName}, {p.firstName}
                        </span>
                        <span className="text-ink-muted block text-xs">
                          {ageFromDob(p.dob)} years old
                        </span>
                      </td>
                      <td className="text-ink-muted px-5 py-2.5 font-mono text-xs">{p.mrn}</td>
                      <td className="text-ink-muted px-5 py-2.5 whitespace-nowrap">
                        {formatDate(p.dob)}
                      </td>
                      <td className="text-ink-muted px-5 py-2.5 capitalize">{p.sex}</td>
                      <td className="text-ink-muted px-5 py-2.5">{p.phone ?? '—'}</td>
                      <td className="px-5 py-2.5">
                        {p.riskLevel && p.riskLevel !== 'none' ? (
                          <Badge tone={riskTones[p.riskLevel]}>{p.riskLevel}</Badge>
                        ) : (
                          <span className="text-ink-faint">—</span>
                        )}
                      </td>
                      <td className="px-5 py-2.5">
                        <SourceBadge source={p.source} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              total={data.total}
              limit={limit}
              offset={offset}
              onPage={setPage}
              noun="patient"
            />
          </Card>
        )}

        {editing && (
          <PatientModal patient={editing === 'new' ? null : editing} onClose={() => setEditing(null)} />
        )}
      </PageBody>
    </>
  )
}
