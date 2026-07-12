import { useRef, useState, type FormEvent } from 'react'
import { roleLabels, type Role } from '../../shared/api/types'
import { Button } from '../../shared/ui/Button'
import { Input, Label, Select, Textarea } from '../../shared/ui/Field'
import { Modal } from '../../shared/ui/Modal'
import { ErrorNote } from '../../shared/ui/Page'
import { useHasRole } from '../../shared/hooks/useRole'
import { usePatientsQuery } from '../patients/api'
import { useRecipientsQuery, useSendMessageMutation } from './api'

const MAX_ATTACHMENTS = 3

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve((reader.result as string).split(',', 2)[1])
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

export function ComposeModal({
  defaultPatientId,
  onClose,
}: {
  defaultPatientId?: string
  onClose: () => void
}) {
  const { data: recipients } = useRecipientsQuery()
  const [recipientIds, setRecipientIds] = useState<string[]>([])
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [patientSearch, setPatientSearch] = useState('')
  const [patientId, setPatientId] = useState(defaultPatientId ?? '')
  const [files, setFiles] = useState<File[]>([])
  const fileRef = useRef<HTMLInputElement>(null)
  const [localError, setLocalError] = useState<string | null>(null)
  const canPickPatient = useHasRole('clinician', 'front_desk')

  const { data: patients } = usePatientsQuery(
    { search: patientSearch || undefined, limit: 20 },
    { skip: !canPickPatient || defaultPatientId !== undefined },
  )

  const [send, { isLoading, error }] = useSendMessageMutation()

  function toggleRecipient(id: string) {
    setRecipientIds((ids) => (ids.includes(id) ? ids.filter((r) => r !== id) : [...ids, id]))
  }

  function onPickFiles(picked: FileList | null) {
    if (!picked) return
    const next = [...files, ...Array.from(picked)].slice(0, MAX_ATTACHMENTS)
    setFiles(next)
    setLocalError(
      files.length + picked.length > MAX_ATTACHMENTS
        ? `At most ${MAX_ATTACHMENTS} attachments per message.`
        : null,
    )
    if (fileRef.current) fileRef.current.value = ''
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (recipientIds.length === 0) return
    const attachments = await Promise.all(
      files.map(async (file) => ({
        filename: file.name,
        contentType: file.type || 'application/octet-stream',
        dataBase64: await fileToBase64(file),
      })),
    )
    const result = await send({
      recipientIds,
      subject,
      body,
      patientId: patientId || null,
      attachments,
    })
    if (!('error' in result)) onClose()
  }

  return (
    <Modal title="New message" open onClose={onClose}>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <Label>To ({recipientIds.length} selected)</Label>
          <div className="border-line max-h-36 space-y-0.5 overflow-y-auto rounded-md border p-2">
            {recipients?.map((r) => (
              <label
                key={r.id}
                className="hover:bg-well flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-[13px]"
              >
                <input
                  type="checkbox"
                  checked={recipientIds.includes(r.id)}
                  onChange={() => toggleRecipient(r.id)}
                  className="accent-primary size-3.5"
                />
                <span className="text-ink">{r.displayName}</span>
                <span className="text-ink-muted text-xs">{roleLabels[r.role as Role] ?? r.role}</span>
              </label>
            ))}
          </div>
        </div>
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

        <div>
          <div className="flex items-center justify-between">
            <Label>Attachments</Label>
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              disabled={files.length >= MAX_ATTACHMENTS}
              className="text-primary text-xs font-semibold hover:underline disabled:opacity-50"
            >
              <i className="iconify tabler--paperclip align-[-2px]" aria-hidden /> Attach file
            </button>
            <input
              ref={fileRef}
              type="file"
              multiple
              accept="image/png,image/jpeg,application/pdf,text/plain,text/csv"
              onChange={(e) => onPickFiles(e.target.files)}
              className="hidden"
            />
          </div>
          {files.length > 0 && (
            <ul className="mt-1 flex flex-wrap gap-1.5">
              {files.map((file, i) => (
                <li
                  key={`${file.name}-${i}`}
                  className="bg-well text-ink inline-flex items-center gap-1 rounded px-2 py-1 text-xs"
                >
                  <i className="iconify tabler--paperclip size-3" aria-hidden />
                  {file.name}
                  <button
                    type="button"
                    onClick={() => setFiles((f) => f.filter((_, j) => j !== i))}
                    className="text-ink-muted hover:text-accent-red ml-0.5"
                    aria-label="Remove attachment"
                  >
                    <i className="iconify tabler--x size-3" aria-hidden />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {localError && <p className="text-accent-red text-xs">{localError}</p>}
        {error !== undefined && <ErrorNote error={error} />}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading || recipientIds.length === 0}>
            <i className="iconify tabler--send" aria-hidden /> Send
          </Button>
        </div>
      </form>
    </Modal>
  )
}
