import { useState, type FormEvent } from 'react'
import { roleLabels, type Role } from '../../shared/api/types'
import { Button } from '../../shared/ui/Button'
import { Input, Select, Textarea } from '../../shared/ui/Field'
import { Modal } from '../../shared/ui/Modal'
import { ErrorNote } from '../../shared/ui/Page'
import { useHasRole } from '../../shared/hooks/useRole'
import { usePatientsQuery } from '../patients/api'
import { useRecipientsQuery, useSendMessageMutation } from './api'

export function ComposeModal({
  defaultPatientId,
  onClose,
}: {
  defaultPatientId?: string
  onClose: () => void
}) {
  const { data: recipients } = useRecipientsQuery()
  const [recipientId, setRecipientId] = useState('')
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [patientSearch, setPatientSearch] = useState('')
  const [patientId, setPatientId] = useState(defaultPatientId ?? '')
  const canPickPatient = useHasRole('clinician', 'front_desk')

  const { data: patients } = usePatientsQuery(
    { search: patientSearch || undefined, limit: 20 },
    { skip: !canPickPatient || defaultPatientId !== undefined },
  )

  const [send, { isLoading, error }] = useSendMessageMutation()

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const result = await send({
      recipientId,
      subject,
      body,
      patientId: patientId || null,
    })
    if (!('error' in result)) onClose()
  }

  return (
    <Modal title="New message" open onClose={onClose}>
      <form onSubmit={onSubmit} className="space-y-4">
        <Select label="To" required value={recipientId} onChange={(e) => setRecipientId(e.target.value)}>
          <option value="" disabled>
            Choose a recipient…
          </option>
          {recipients?.map((r) => (
            <option key={r.id} value={r.id}>
              {r.displayName} — {roleLabels[r.role as Role] ?? r.role}
            </option>
          ))}
        </Select>
        <Input
          label="Subject"
          required
          placeholder="Reschedule request, lab follow-up…"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
        />
        {canPickPatient && defaultPatientId === undefined && (
          <div className="space-y-2">
            <Input
              label="About patient (optional)"
              icon="tabler--search"
              placeholder="Search by name or identifier…"
              value={patientSearch}
              onChange={(e) => setPatientSearch(e.target.value)}
            />
            <Select value={patientId} onChange={(e) => setPatientId(e.target.value)}>
              <option value="">No patient link</option>
              {patients?.items.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.lastName}, {p.firstName} ({p.mrn})
                </option>
              ))}
            </Select>
          </div>
        )}
        <Textarea
          label="Message"
          required
          placeholder="Write your message…"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          className="min-h-32"
        />
        {error !== undefined && <ErrorNote error={error} />}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading || !recipientId}>
            <i className="iconify tabler--send" aria-hidden /> Send
          </Button>
        </div>
      </form>
    </Modal>
  )
}
