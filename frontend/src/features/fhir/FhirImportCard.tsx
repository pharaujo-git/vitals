import { useState, type FormEvent } from 'react'
import { Button } from '../../shared/ui/Button'
import { Input, Textarea } from '../../shared/ui/Field'
import { Card, ErrorNote } from '../../shared/ui/Page'
import type { ImportBatch } from '../import/types'
import { useImportFhirMutation } from './api'

export function FhirImportCard() {
  const [label, setLabel] = useState('')
  const [content, setContent] = useState('')
  const [importFhir, { isLoading, error }] = useImportFhirMutation()
  const [result, setResult] = useState<ImportBatch | null>(null)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const r = await importFhir({ label: label || 'FHIR import', content })
    if ('data' in r && r.data) {
      setResult(r.data)
      setContent('')
      setLabel('')
    }
  }

  return (
    <Card title="FHIR resources">
      <form onSubmit={onSubmit} className="space-y-3">
        <p className="text-ink-muted text-xs">
          Paste a FHIR R4 <code className="bg-well rounded px-1">Bundle</code> (or a single{' '}
          <code className="bg-well rounded px-1">Patient</code> /{' '}
          <code className="bg-well rounded px-1">Observation</code>) as JSON. Resources are
          validated against the FHIR schema, then mapped by MRN identifier and LOINC code.
        </p>
        <Textarea
          label="Resource JSON"
          placeholder='{"resourceType": "Bundle", "type": "collection", "entry": [...]}'
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="min-h-44 font-mono text-xs"
        />
        <Input
          label="Label"
          placeholder="Regional exchange bundle"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
        />
        {error !== undefined && <ErrorNote error={error} />}
        {result && (
          <p className="text-ink-muted text-xs">
            Imported <span className="text-accent-green font-semibold">{result.importedCount}</span> of{' '}
            {result.totalRecords} resources
            {result.errorCount > 0 && (
              <>
                {' '}
                — <span className="text-accent-red font-semibold">{result.errorCount} errors</span>
              </>
            )}
            .
          </p>
        )}
        <div className="flex justify-end">
          <Button type="submit" disabled={isLoading || !content.trim()}>
            <i className="iconify tabler--flame" aria-hidden /> Import FHIR
          </Button>
        </div>
      </form>
    </Card>
  )
}
