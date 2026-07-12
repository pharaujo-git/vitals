import { useState, type FormEvent, type ReactNode } from 'react'
import { formatDate } from '../../shared/lib/format'
import { Badge } from '../../shared/ui/Badge'
import { Button } from '../../shared/ui/Button'
import { Input, Select } from '../../shared/ui/Field'
import { Card, Spinner } from '../../shared/ui/Page'
import {
  useAddAllergyMutation,
  useAddMedicationMutation,
  useAddProblemMutation,
  useClinicalListsQuery,
  useDeleteAllergyMutation,
  useDeleteMedicationMutation,
  useDeleteProblemMutation,
  useUpdateMedicationMutation,
  useUpdateProblemMutation,
} from './api'
import type { Allergy, Medication, Problem } from './types'

const severityTones = { mild: 'muted', moderate: 'amber', severe: 'red' } as const

function Section({
  title,
  icon,
  onAdd,
  adding,
  children,
}: {
  title: string
  icon: string
  onAdd: () => void
  adding: boolean
  children: ReactNode
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <p className="text-ink-muted flex items-center gap-1.5 text-xs font-bold tracking-wide uppercase">
          <i className={`iconify ${icon} size-4`} aria-hidden />
          {title}
        </p>
        <Button size="sm" variant="ghost" onClick={onAdd}>
          <i className={`iconify ${adding ? 'tabler--x' : 'tabler--plus'}`} aria-hidden />
          {adding ? 'Cancel' : 'Add'}
        </Button>
      </div>
      {children}
    </div>
  )
}

function RowActions({ onDelete, extra }: { onDelete: () => void; extra?: ReactNode }) {
  return (
    <span className="ml-auto flex shrink-0 items-center gap-0.5">
      {extra}
      <button
        onClick={onDelete}
        className="text-ink-faint hover:text-accent-red flex size-6 items-center justify-center rounded"
        aria-label="Remove"
        title="Remove (entered in error)"
      >
        <i className="iconify tabler--trash size-3.5" aria-hidden />
      </button>
    </span>
  )
}

function ProblemsSection({ patientId, problems }: { patientId: string; problems: Problem[] }) {
  const [adding, setAdding] = useState(false)
  const [description, setDescription] = useState('')
  const [icdCode, setIcdCode] = useState('')
  const [onset, setOnset] = useState('')
  const [add, { isLoading }] = useAddProblemMutation()
  const [update] = useUpdateProblemMutation()
  const [remove] = useDeleteProblemMutation()

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const result = await add({
      patientId,
      description,
      icdCode: icdCode.trim() || null,
      status: 'active',
      onsetDate: onset || null,
    })
    if (!('error' in result)) {
      setDescription('')
      setIcdCode('')
      setOnset('')
      setAdding(false)
    }
  }

  return (
    <Section title="Problem list" icon="tabler--clipboard-heart" onAdd={() => setAdding((v) => !v)} adding={adding}>
      {adding && (
        <form onSubmit={onSubmit} className="mb-2 space-y-2">
          <Input
            placeholder="Condition, e.g. Type 2 diabetes"
            required
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <div className="grid grid-cols-2 gap-2">
            <Input placeholder="ICD-10 (optional)" value={icdCode} onChange={(e) => setIcdCode(e.target.value)} />
            <Input type="date" value={onset} onChange={(e) => setOnset(e.target.value)} />
          </div>
          <Button type="submit" size="sm" disabled={isLoading} className="w-full">
            Add problem
          </Button>
        </form>
      )}
      {problems.length === 0 && !adding && <p className="text-ink-faint text-xs">No known problems.</p>}
      <ul className="space-y-1.5">
        {problems.map((p) => (
          <li key={p.id} className="flex items-center gap-2 text-[13px]">
            <Badge tone={p.status === 'active' ? 'amber' : 'green'}>{p.status}</Badge>
            <span className={`text-ink min-w-0 truncate ${p.status === 'resolved' ? 'line-through opacity-60' : ''}`}>
              {p.description}
              {p.icdCode && <span className="text-ink-faint ml-1 font-mono text-[11px]">{p.icdCode}</span>}
            </span>
            {p.onsetDate && (
              <span className="text-ink-faint shrink-0 text-[11px]">since {formatDate(p.onsetDate)}</span>
            )}
            <RowActions
              onDelete={() => remove(p.id)}
              extra={
                <button
                  onClick={() =>
                    update({
                      id: p.id,
                      description: p.description,
                      icdCode: p.icdCode,
                      status: p.status === 'active' ? 'resolved' : 'active',
                      onsetDate: p.onsetDate,
                    })
                  }
                  className="text-ink-faint hover:text-accent-green flex size-6 items-center justify-center rounded"
                  aria-label={p.status === 'active' ? 'Mark resolved' : 'Reactivate'}
                  title={p.status === 'active' ? 'Mark resolved' : 'Reactivate'}
                >
                  <i
                    className={`iconify ${p.status === 'active' ? 'tabler--check' : 'tabler--rotate'} size-3.5`}
                    aria-hidden
                  />
                </button>
              }
            />
          </li>
        ))}
      </ul>
    </Section>
  )
}

function MedicationsSection({ patientId, medications }: { patientId: string; medications: Medication[] }) {
  const [adding, setAdding] = useState(false)
  const [name, setName] = useState('')
  const [dose, setDose] = useState('')
  const [frequency, setFrequency] = useState('')
  const [add, { isLoading }] = useAddMedicationMutation()
  const [update] = useUpdateMedicationMutation()
  const [remove] = useDeleteMedicationMutation()

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const result = await add({
      patientId,
      name,
      dose: dose.trim() || null,
      frequency: frequency.trim() || null,
      active: true,
      startedDate: null,
    })
    if (!('error' in result)) {
      setName('')
      setDose('')
      setFrequency('')
      setAdding(false)
    }
  }

  return (
    <Section title="Medications" icon="tabler--pill" onAdd={() => setAdding((v) => !v)} adding={adding}>
      {adding && (
        <form onSubmit={onSubmit} className="mb-2 space-y-2">
          <Input placeholder="Medication, e.g. Metformin" required value={name} onChange={(e) => setName(e.target.value)} />
          <div className="grid grid-cols-2 gap-2">
            <Input placeholder="Dose, e.g. 500 mg" value={dose} onChange={(e) => setDose(e.target.value)} />
            <Input placeholder="Frequency, e.g. 2x daily" value={frequency} onChange={(e) => setFrequency(e.target.value)} />
          </div>
          <Button type="submit" size="sm" disabled={isLoading} className="w-full">
            Add medication
          </Button>
        </form>
      )}
      {medications.length === 0 && !adding && <p className="text-ink-faint text-xs">No medications recorded.</p>}
      <ul className="space-y-1.5">
        {medications.map((m) => (
          <li key={m.id} className="flex items-center gap-2 text-[13px]">
            <Badge tone={m.active ? 'blue' : 'muted'}>{m.active ? 'active' : 'stopped'}</Badge>
            <span className={`text-ink min-w-0 truncate ${m.active ? '' : 'line-through opacity-60'}`}>
              {m.name}
              {(m.dose || m.frequency) && (
                <span className="text-ink-muted ml-1 text-xs">
                  {[m.dose, m.frequency].filter(Boolean).join(' · ')}
                </span>
              )}
            </span>
            <RowActions
              onDelete={() => remove(m.id)}
              extra={
                m.active ? (
                  <button
                    onClick={() =>
                      update({
                        id: m.id,
                        name: m.name,
                        dose: m.dose,
                        frequency: m.frequency,
                        active: false,
                        startedDate: m.startedDate,
                      })
                    }
                    className="text-ink-faint hover:text-accent-amber flex size-6 items-center justify-center rounded"
                    aria-label="Stop medication"
                    title="Stop medication"
                  >
                    <i className="iconify tabler--player-stop size-3.5" aria-hidden />
                  </button>
                ) : undefined
              }
            />
          </li>
        ))}
      </ul>
    </Section>
  )
}

function AllergiesSection({ patientId, allergies }: { patientId: string; allergies: Allergy[] }) {
  const [adding, setAdding] = useState(false)
  const [substance, setSubstance] = useState('')
  const [reaction, setReaction] = useState('')
  const [severity, setSeverity] = useState('moderate')
  const [add, { isLoading }] = useAddAllergyMutation()
  const [remove] = useDeleteAllergyMutation()

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const result = await add({ patientId, substance, reaction: reaction.trim() || null, severity })
    if (!('error' in result)) {
      setSubstance('')
      setReaction('')
      setSeverity('moderate')
      setAdding(false)
    }
  }

  return (
    <Section title="Allergies" icon="tabler--alert-octagon" onAdd={() => setAdding((v) => !v)} adding={adding}>
      {adding && (
        <form onSubmit={onSubmit} className="mb-2 space-y-2">
          <Input placeholder="Substance, e.g. Penicillin" required value={substance} onChange={(e) => setSubstance(e.target.value)} />
          <div className="grid grid-cols-2 gap-2">
            <Input placeholder="Reaction (optional)" value={reaction} onChange={(e) => setReaction(e.target.value)} />
            <Select value={severity} onChange={(e) => setSeverity(e.target.value)}>
              <option value="mild">Mild</option>
              <option value="moderate">Moderate</option>
              <option value="severe">Severe</option>
            </Select>
          </div>
          <Button type="submit" size="sm" disabled={isLoading} className="w-full">
            Add allergy
          </Button>
        </form>
      )}
      {allergies.length === 0 && !adding && <p className="text-ink-faint text-xs">No known allergies.</p>}
      <ul className="space-y-1.5">
        {allergies.map((a) => (
          <li key={a.id} className="flex items-center gap-2 text-[13px]">
            <Badge tone={severityTones[a.severity]}>{a.severity}</Badge>
            <span className="text-ink min-w-0 truncate">
              {a.substance}
              {a.reaction && <span className="text-ink-muted ml-1 text-xs">— {a.reaction}</span>}
            </span>
            <RowActions onDelete={() => remove(a.id)} />
          </li>
        ))}
      </ul>
    </Section>
  )
}

/** Structured clinical lists: problem list, medications, allergies. */
export function ClinicalListsCard({ patientId }: { patientId: string }) {
  const { data, isLoading } = useClinicalListsQuery(patientId)
  return (
    <Card title="Clinical lists">
      {isLoading && <Spinner />}
      {data && (
        <div className="space-y-5">
          <ProblemsSection patientId={patientId} problems={data.problems} />
          <MedicationsSection patientId={patientId} medications={data.medications} />
          <AllergiesSection patientId={patientId} allergies={data.allergies} />
        </div>
      )}
    </Card>
  )
}
