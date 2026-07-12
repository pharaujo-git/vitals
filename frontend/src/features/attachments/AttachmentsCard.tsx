import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useAppSelector } from '../../app/hooks'
import { formatDateTime } from '../../shared/lib/format'
import { Badge } from '../../shared/ui/Badge'
import { Button } from '../../shared/ui/Button'
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog'
import { Input, Select } from '../../shared/ui/Field'
import { Modal } from '../../shared/ui/Modal'
import { Card, EmptyState, ErrorNote, Spinner } from '../../shared/ui/Page'
import {
  useAttachmentsQuery,
  useDeleteAttachmentMutation,
  useUploadAttachmentMutation,
  type Attachment,
} from './api'

function formatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`
  return `${bytes} B`
}

function fileIcon(a: Attachment): string {
  if (a.contentType.startsWith('image/')) return 'tabler--photo'
  if (a.contentType === 'application/pdf') return 'tabler--file-type-pdf'
  if (a.contentType === 'application/dicom') return 'tabler--radioactive'
  return 'tabler--file'
}

/** Fetch the file with the auth header (an <img src> can't send one) and
 *  preview it via an object URL. */
function PreviewModal({ attachment, onClose }: { attachment: Attachment; onClose: () => void }) {
  const token = useAppSelector((s) => s.auth.accessToken)
  const [url, setUrl] = useState<string | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let objectUrl: string | null = null
    fetch(`/api/attachments/${attachment.id}/content`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error(String(response.status))
        objectUrl = URL.createObjectURL(await response.blob())
        setUrl(objectUrl)
      })
      .catch(() => setFailed(true))
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [attachment.id, token])

  const isImage = attachment.contentType.startsWith('image/')
  const isPdf = attachment.contentType === 'application/pdf'

  return (
    <Modal title={attachment.filename} open onClose={onClose} wide>
      {failed && <ErrorNote error={{ data: { detail: 'Could not load the file.' } }} />}
      {!url && !failed && <Spinner />}
      {url && isImage && (
        <img src={url} alt={attachment.description ?? attachment.filename} className="mx-auto max-h-[70vh] rounded-md" />
      )}
      {url && isPdf && <iframe src={url} title={attachment.filename} className="h-[70vh] w-full rounded-md" />}
      {url && !isImage && !isPdf && (
        <p className="text-ink-muted text-[13px]">
          No inline preview for {attachment.contentType}. Use download instead.
        </p>
      )}
      {url && (
        <div className="mt-4 flex justify-end">
          <a href={url} download={attachment.filename}>
            <Button variant="secondary">
              <i className="iconify tabler--download" aria-hidden /> Download
            </Button>
          </a>
        </div>
      )}
    </Modal>
  )
}

export function AttachmentsCard({ patientId }: { patientId: string }) {
  const { data, isLoading } = useAttachmentsQuery(patientId)
  const [upload, { isLoading: uploading, error }] = useUploadAttachmentMutation()
  const [remove, { isLoading: removing }] = useDeleteAttachmentMutation()
  const [kind, setKind] = useState('imaging')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const [viewing, setViewing] = useState<Attachment | null>(null)
  const [deleting, setDeleting] = useState<Attachment | null>(null)

  async function onUpload(e: FormEvent) {
    e.preventDefault()
    if (!file) return
    const result = await upload({ patientId, file, kind, description: description.trim() || null })
    if (!('error' in result)) {
      setFile(null)
      setDescription('')
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  return (
    <Card title="Imaging & documents">
      <form onSubmit={onUpload} className="border-line mb-4 space-y-2 border-b border-dashed pb-4">
        <div className="flex flex-wrap items-center gap-2">
          <input
            ref={fileRef}
            type="file"
            accept="image/png,image/jpeg,application/pdf,application/dicom"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="text-ink-muted file:bg-well file:text-ink file:border-line min-w-0 flex-1 text-xs file:mr-3 file:cursor-pointer file:rounded-md file:border file:px-3 file:py-1.5 file:text-xs file:font-semibold"
          />
          <div className="w-32">
            <Select value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="imaging">Imaging</option>
              <option value="document">Document</option>
            </Select>
          </div>
        </div>
        <div className="flex gap-2">
          <Input
            placeholder="Description, e.g. Chest X-ray PA view…"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <Button type="submit" disabled={uploading || !file}>
            <i className="iconify tabler--upload" aria-hidden />
            {uploading ? 'Uploading…' : 'Upload'}
          </Button>
        </div>
        <p className="text-ink-faint text-[11px]">PNG, JPEG, PDF or DICOM · up to 10 MB.</p>
        {error !== undefined && <ErrorNote error={error} />}
      </form>

      {isLoading && <Spinner />}
      {data && data.length === 0 && (
        <EmptyState icon="tabler--photo-off" message="No imaging or documents attached yet." />
      )}
      {data && data.length > 0 && (
        <ul className="divide-line -mx-5 -mb-5 divide-y">
          {data.map((a) => (
            <li key={a.id} className="flex items-center gap-3 px-5 py-2.5">
              <button
                onClick={() => setViewing(a)}
                className="flex min-w-0 flex-1 items-center gap-3 text-left"
              >
                <span className="bg-well text-ink-muted flex size-9 shrink-0 items-center justify-center rounded-md">
                  <i className={`iconify ${fileIcon(a)} size-4.5`} aria-hidden />
                </span>
                <span className="min-w-0">
                  <span className="text-ink block truncate text-[13px] font-medium hover:underline">
                    {a.description || a.filename}
                  </span>
                  <span className="text-ink-muted block truncate text-xs">
                    {formatSize(a.size)} · {formatDateTime(a.createdAt)}
                    {a.uploadedByName ? ` · ${a.uploadedByName}` : ''}
                  </span>
                </span>
              </button>
              <Badge tone={a.kind === 'imaging' ? 'violet' : 'blue'}>{a.kind}</Badge>
              <button
                onClick={() => setDeleting(a)}
                className="text-ink-faint hover:text-accent-red flex size-7 shrink-0 items-center justify-center rounded-md"
                aria-label="Delete attachment"
              >
                <i className="iconify tabler--trash size-4" aria-hidden />
              </button>
            </li>
          ))}
        </ul>
      )}

      {viewing && <PreviewModal attachment={viewing} onClose={() => setViewing(null)} />}
      {deleting && (
        <ConfirmDialog
          open
          title="Delete attachment"
          message={`Delete "${deleting.description || deleting.filename}" from this record?`}
          busy={removing}
          onConfirm={async () => {
            await remove(deleting.id)
            setDeleting(null)
          }}
          onClose={() => setDeleting(null)}
        />
      )}
    </Card>
  )
}
