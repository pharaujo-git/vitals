import { useRef, useState, type FormEvent } from 'react'
import { usePagination } from '../../shared/hooks/usePagination'
import { formatDateTime } from '../../shared/lib/format'
import { Badge } from '../../shared/ui/Badge'
import { Button } from '../../shared/ui/Button'
import { Input, Label, Textarea } from '../../shared/ui/Field'
import { Modal } from '../../shared/ui/Modal'
import { Card, EmptyState, ErrorNote, PageBody, PageHeader, Spinner } from '../../shared/ui/Page'
import { Pagination } from '../../shared/ui/Pagination'
import { FhirImportCard } from '../fhir/FhirImportCard'
import {
  useImportBatchesQuery,
  useImportCsvMutation,
  useImportHl7Mutation,
  useImportIssuesQuery,
} from './api'
import type { ImportBatch } from './types'

const CSV_SAMPLE = `mrn,first_name,last_name,dob,sex,code,value,taken_at
MRN-EXT-001,Jane,Doe,1975-04-02,f,bp_systolic,152,2026-07-01T09:15:00
MRN-EXT-001,Jane,Doe,1975-04-02,f,glucose,131,2026-07-01T09:20:00
MRN-EXT-002,John,Roe,1990-11-23,m,,,`

const HL7_SAMPLE = `MSH|^~\\&|EXTERN_LAB|20260701120000
PID|MRN-EXT-003|Souza^Carlos|19621108|M
OBX|8867-4|88|bpm|20260701120000
OBX|8480-6|161|mmHg|20260701120000
OBX|4548-4|8.1|%|20260701120000`

function CsvImportCard() {
  const [label, setLabel] = useState('')
  const [content, setContent] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const [importCsv, { isLoading, error }] = useImportCsvMutation()
  const [result, setResult] = useState<ImportBatch | null>(null)

  async function onFile(file: File) {
    setContent(await file.text())
    if (!label) setLabel(file.name)
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const r = await importCsv({ label: label || 'CSV import', content })
    if ('data' in r && r.data) {
      setResult(r.data)
      setContent('')
      setLabel('')
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  return (
    <Card title="CSV file">
      <form onSubmit={onSubmit} className="space-y-3">
        <p className="text-ink-muted text-xs">
          Header row with <code className="bg-well rounded px-1">mrn, first_name, last_name, dob</code>{' '}
          plus optional <code className="bg-well rounded px-1">sex, code, value, taken_at</code> for
          observations. Rows that fail mapping are reported below, not dropped.
        </p>
        <div>
          <Label>File</Label>
          <input
            ref={fileRef}
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
            className="text-ink-muted file:bg-well file:text-ink file:border-line block w-full text-xs file:mr-3 file:cursor-pointer file:rounded-md file:border file:px-3 file:py-1.5 file:text-xs file:font-semibold"
          />
        </div>
        <Textarea
          label="Or paste CSV"
          placeholder={CSV_SAMPLE}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="min-h-28 font-mono text-xs"
        />
        <Input label="Label" placeholder="July lab feed" value={label} onChange={(e) => setLabel(e.target.value)} />
        {error !== undefined && <ErrorNote error={error} />}
        {result && (
          <p className="text-ink-muted text-xs">
            Imported <span className="text-accent-green font-semibold">{result.importedCount}</span> of{' '}
            {result.totalRecords} records
            {result.errorCount > 0 && (
              <>
                {' '}
                — <span className="text-accent-red font-semibold">{result.errorCount} errors</span> (see
                batch below)
              </>
            )}
            .
          </p>
        )}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={() => setContent(CSV_SAMPLE)}>
            Use sample
          </Button>
          <Button type="submit" disabled={isLoading || !content.trim()}>
            <i className="iconify tabler--file-import" aria-hidden /> Import CSV
          </Button>
        </div>
      </form>
    </Card>
  )
}

function Hl7ImportCard() {
  const [label, setLabel] = useState('')
  const [content, setContent] = useState('')
  const [importHl7, { isLoading, error }] = useImportHl7Mutation()
  const [result, setResult] = useState<ImportBatch | null>(null)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const r = await importHl7({ label: label || 'HL7 message feed', content })
    if ('data' in r && r.data) {
      setResult(r.data)
      setContent('')
      setLabel('')
    }
  }

  return (
    <Card title="HL7-style messages">
      <form onSubmit={onSubmit} className="space-y-3">
        <p className="text-ink-muted text-xs">
          Pipe-delimited segments: <code className="bg-well rounded px-1">PID</code> starts a patient,{' '}
          <code className="bg-well rounded px-1">OBX</code> adds an observation by LOINC code. Bad
          segments are reported per line.
        </p>
        <Textarea
          label="Message content"
          placeholder={HL7_SAMPLE}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="min-h-44 font-mono text-xs"
        />
        <Input label="Label" placeholder="External lab HL7" value={label} onChange={(e) => setLabel(e.target.value)} />
        {error !== undefined && <ErrorNote error={error} />}
        {result && (
          <p className="text-ink-muted text-xs">
            Imported <span className="text-accent-green font-semibold">{result.importedCount}</span> of{' '}
            {result.totalRecords} records
            {result.errorCount > 0 && (
              <>
                {' '}
                — <span className="text-accent-red font-semibold">{result.errorCount} errors</span>
              </>
            )}
            .
          </p>
        )}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={() => setContent(HL7_SAMPLE)}>
            Use sample
          </Button>
          <Button type="submit" disabled={isLoading || !content.trim()}>
            <i className="iconify tabler--message-2-code" aria-hidden /> Import messages
          </Button>
        </div>
      </form>
    </Card>
  )
}

function IssuesModal({ batch, onClose }: { batch: ImportBatch; onClose: () => void }) {
  const { limit, offset, setPage } = usePagination()
  const { data, isLoading } = useImportIssuesQuery({ batchId: batch.id, limit, offset })
  return (
    <Modal title={`Mapping errors — ${batch.label}`} open onClose={onClose} wide>
      {isLoading && <Spinner />}
      {data && data.items.length === 0 && (
        <EmptyState icon="tabler--circle-check" message="No mapping errors in this batch." />
      )}
      {data && data.items.length > 0 && (
        <div className="border-line -m-2 rounded-md border">
          <table className="w-full text-[12.5px]">
            <thead>
              <tr className="bg-well text-ink-muted border-line border-b text-left text-[10.5px] font-bold tracking-[0.08em] uppercase">
                <th className="px-4 py-2">Record</th>
                <th className="px-4 py-2">Error</th>
                <th className="px-4 py-2">Raw data</th>
              </tr>
            </thead>
            <tbody className="divide-line divide-y">
              {data.items.map((issue) => (
                <tr key={issue.id}>
                  <td className="text-ink-muted px-4 py-2">#{issue.recordNumber}</td>
                  <td className="text-accent-red px-4 py-2">{issue.message}</td>
                  <td className="text-ink-faint max-w-64 truncate px-4 py-2 font-mono text-[11px]">
                    {issue.raw}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination total={data.total} limit={limit} offset={offset} onPage={setPage} noun="error" />
        </div>
      )}
    </Modal>
  )
}

export function ImportPage() {
  const { limit, offset, setPage } = usePagination(10)
  const { data, isLoading } = useImportBatchesQuery({ limit, offset })
  const [viewing, setViewing] = useState<ImportBatch | null>(null)

  return (
    <>
      <PageHeader title="Data import" />
      <PageBody>
        <div className="mb-4 grid gap-4 lg:grid-cols-2">
          <CsvImportCard />
          <Hl7ImportCard />
          <FhirImportCard />
        </div>

        <Card title="Import history" flush>
          {isLoading && <Spinner />}
          {data && data.items.length === 0 && (
            <div className="p-5">
              <EmptyState icon="tabler--database-import" message="No imports yet." />
            </div>
          )}
          {data && data.items.length > 0 && (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-[13px]">
                  <thead>
                    <tr className="bg-well text-ink-muted border-line border-b text-left text-[10.5px] font-bold tracking-[0.08em] uppercase">
                      <th className="px-5 py-2.5">When</th>
                      <th className="px-5 py-2.5">Label</th>
                      <th className="px-5 py-2.5">Format</th>
                      <th className="px-5 py-2.5 text-right">Records</th>
                      <th className="px-5 py-2.5 text-right">Imported</th>
                      <th className="px-5 py-2.5 text-right">Errors</th>
                    </tr>
                  </thead>
                  <tbody className="divide-line divide-y">
                    {data.items.map((b) => (
                      <tr
                        key={b.id}
                        onClick={() => setViewing(b)}
                        className="hover:bg-well/60 cursor-pointer transition-colors"
                      >
                        <td className="text-ink-muted px-5 py-2.5 whitespace-nowrap">
                          {formatDateTime(b.createdAt)}
                        </td>
                        <td className="text-ink px-5 py-2.5 font-medium">{b.label}</td>
                        <td className="px-5 py-2.5">
                          <Badge tone={b.format === 'csv' ? 'blue' : b.format === 'hl7' ? 'violet' : 'green'}>
                            {b.format.toUpperCase()}
                          </Badge>
                        </td>
                        <td className="text-ink-muted px-5 py-2.5 text-right tabular-nums">
                          {b.totalRecords}
                        </td>
                        <td className="text-accent-green px-5 py-2.5 text-right font-semibold tabular-nums">
                          {b.importedCount}
                        </td>
                        <td
                          className={`px-5 py-2.5 text-right font-semibold tabular-nums ${
                            b.errorCount > 0 ? 'text-accent-red' : 'text-ink-faint'
                          }`}
                        >
                          {b.errorCount}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination total={data.total} limit={limit} offset={offset} onPage={setPage} noun="batch" />
            </>
          )}
        </Card>

        {viewing && <IssuesModal batch={viewing} onClose={() => setViewing(null)} />}
      </PageBody>
    </>
  )
}
