import { useState, type FormEvent } from 'react'
import { Button } from '../../shared/ui/Button'
import { Input, Label, Select, Textarea } from '../../shared/ui/Field'
import { Modal } from '../../shared/ui/Modal'
import { ErrorNote } from '../../shared/ui/Page'
import { todayIso } from '../../shared/lib/format'
import { useCreateEncounterMutation, useObservationCatalogQuery } from './api'
import { encounterTypeLabels } from './types'

interface ObservationRow {
  code: string
  value: string
}

export function EncounterModal({ patientId, onClose }: { patientId: string; onClose: () => void }) {
  const { data: catalog } = useObservationCatalogQuery()
  const [date, setDate] = useState(todayIso())
  const [time, setTime] = useState('09:00')
  const [encounterType, setEncounterType] = useState('visit')
  const [reason, setReason] = useState('')
  const [notes, setNotes] = useState('')
  const [rows, setRows] = useState<ObservationRow[]>([{ code: 'heart_rate', value: '' }])

  const [create, { isLoading, error }] = useCreateEncounterMutation()

  function setRow(index: number, patch: Partial<ObservationRow>) {
    setRows((r) => r.map((row, i) => (i === index ? { ...row, ...patch } : row)))
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const observations = rows
      .filter((r) => r.value.trim() !== '')
      .map((r) => {
        const type = catalog?.find((t) => t.code === r.code)
        return type?.kind === 'text'
          ? { code: r.code, valueNum: null, valueText: r.value }
          : { code: r.code, valueNum: Number(r.value), valueText: null }
      })
    const result = await create({
      patientId,
      occurredAt: new Date(`${date}T${time}:00`).toISOString(),
      encounterType,
      reason: reason.trim() || null,
      notes: notes.trim() || null,
      observations,
    })
    if (!('error' in result)) onClose()
  }

  return (
    <Modal title="New encounter" open onClose={onClose} wide>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="grid grid-cols-3 gap-3">
          <Input label="Date" type="date" required value={date} onChange={(e) => setDate(e.target.value)} />
          <Input label="Time" type="time" required value={time} onChange={(e) => setTime(e.target.value)} />
          <Select
            label="Type"
            value={encounterType}
            onChange={(e) => setEncounterType(e.target.value)}
          >
            {Object.entries(encounterTypeLabels)
              .filter(([code]) => code !== 'imported')
              .map(([code, label]) => (
                <option key={code} value={code}>
                  {label}
                </option>
              ))}
          </Select>
        </div>
        <Input
          label="Reason"
          placeholder="Annual physical, chest pain…"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />

        <div>
          <Label>Observations</Label>
          <div className="space-y-2">
            {rows.map((row, i) => {
              const type = catalog?.find((t) => t.code === row.code)
              return (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-56">
                    <Select value={row.code} onChange={(e) => setRow(i, { code: e.target.value, value: '' })}>
                      {catalog?.map((t) => (
                        <option key={t.code} value={t.code}>
                          {t.label}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div className="flex-1">
                    {type?.kind === 'text' ? (
                      <Input
                        placeholder="Note text…"
                        value={row.value}
                        onChange={(e) => setRow(i, { value: e.target.value })}
                      />
                    ) : (
                      <Input
                        type="number"
                        step="any"
                        placeholder={
                          type ? `${type.minValue}–${type.maxValue} ${type.unit ?? ''}` : 'Value'
                        }
                        value={row.value}
                        onChange={(e) => setRow(i, { value: e.target.value })}
                      />
                    )}
                  </div>
                  <span className="text-ink-muted w-16 text-xs">{type?.kind === 'text' ? '' : (type?.unit ?? '')}</span>
                  <button
                    type="button"
                    onClick={() => setRows((r) => r.filter((_, j) => j !== i))}
                    disabled={rows.length === 1}
                    className="text-ink-muted hover:text-accent-red flex size-7 items-center justify-center rounded-md disabled:opacity-30"
                    aria-label="Remove observation"
                  >
                    <i className="iconify tabler--trash size-4" aria-hidden />
                  </button>
                </div>
              )
            })}
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="mt-2"
            onClick={() => setRows((r) => [...r, { code: 'heart_rate', value: '' }])}
          >
            <i className="iconify tabler--plus" aria-hidden /> Add observation
          </Button>
        </div>

        <Textarea
          label="Notes"
          placeholder="Visit documentation…"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
        {error !== undefined && <ErrorNote error={error} />}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            Save encounter
          </Button>
        </div>
      </form>
    </Modal>
  )
}
