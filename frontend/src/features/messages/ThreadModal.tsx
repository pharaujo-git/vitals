import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAppSelector } from '../../app/hooks'
import type { MessageAttachment } from './types'
import { formatDateTime } from '../../shared/lib/format'
import { Badge } from '../../shared/ui/Badge'
import { Button } from '../../shared/ui/Button'
import { Textarea } from '../../shared/ui/Field'
import { Modal } from '../../shared/ui/Modal'
import { ErrorNote, Spinner } from '../../shared/ui/Page'
import { useOpenThreadMutation, useSendMessageMutation } from './api'
import type { Message } from './types'

function AttachmentChip({ attachment }: { attachment: MessageAttachment }) {
  const token = useAppSelector((s) => s.auth.accessToken)

  async function download() {
    const response = await fetch(`/api/messages/attachments/${attachment.id}/content`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    })
    if (!response.ok) return
    const url = URL.createObjectURL(await response.blob())
    const a = document.createElement('a')
    a.href = url
    a.download = attachment.filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <button
      onClick={download}
      className="bg-surface border-line text-ink hover:border-primary hover:text-primary inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[11px] font-semibold"
      title={`Download (${Math.max(1, Math.round(attachment.size / 1024))} KB)`}
    >
      <i className="iconify tabler--paperclip size-3" aria-hidden />
      {attachment.filename}
    </button>
  )
}

export function ThreadModal({ message, onClose }: { message: Message; onClose: () => void }) {
  const me = useAppSelector((s) => s.auth.user)
  const [openThread, { data: thread, isLoading }] = useOpenThreadMutation()
  const [reply, setReply] = useState('')
  const [send, { isLoading: sending, error }] = useSendMessageMutation()

  useEffect(() => {
    openThread(message.id)
  }, [message.id, openThread])

  const latest = thread?.[thread.length - 1]
  const patientId = latest?.patientId ?? message.patientId
  const patientName = latest?.patientName ?? message.patientName

  async function onReply(e: FormEvent) {
    e.preventDefault()
    if (!latest || !me) return
    // Reply goes to the other participant of the latest message.
    const otherId = latest.senderId === me.id ? latest.recipientId : latest.senderId
    const result = await send({
      recipientIds: [otherId],
      subject: message.subject.startsWith('Re: ') ? message.subject : `Re: ${message.subject}`,
      body: reply,
      parentId: latest.id,
    })
    if (!('error' in result)) {
      setReply('')
      openThread(message.id)
    }
  }

  return (
    <Modal title={message.subject} open onClose={onClose} wide>
      {patientId && patientName && (
        <Link
          to={`/patients/${patientId}`}
          onClick={onClose}
          className="mb-3 inline-flex"
          title="Open patient record"
        >
          <Badge tone="primary">
            <i className="iconify tabler--user size-3" aria-hidden />
            {patientName}
          </Badge>
        </Link>
      )}

      {isLoading && <Spinner />}
      {thread && (
        <div className="max-h-96 space-y-3 overflow-y-auto pr-1">
          {thread.map((m) => {
            const mine = m.senderId === me?.id
            return (
              <div key={m.id} className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-lg px-3.5 py-2.5 ${
                    mine ? 'bg-primary/12 border-primary/20 border' : 'bg-well border-line border'
                  }`}
                >
                  <p className="text-ink-muted mb-1 text-[11px] font-semibold">
                    {mine ? 'You' : m.senderName} → {m.recipientId === me?.id ? 'you' : m.recipientName}
                    <span className="text-ink-faint ml-2 font-normal">
                      {formatDateTime(m.createdAt)}
                    </span>
                  </p>
                  <p className="text-ink text-[13px] whitespace-pre-wrap">{m.body}</p>
                  {m.attachments.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {m.attachments.map((attachment) => (
                        <AttachmentChip key={attachment.id} attachment={attachment} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      <form onSubmit={onReply} className="border-line mt-4 space-y-3 border-t pt-4">
        <Textarea
          placeholder="Write a reply…"
          required
          value={reply}
          onChange={(e) => setReply(e.target.value)}
          className="min-h-20"
        />
        {error !== undefined && <ErrorNote error={error} />}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Close
          </Button>
          <Button type="submit" disabled={sending || !reply.trim()}>
            <i className="iconify tabler--arrow-back-up" aria-hidden /> Reply
          </Button>
        </div>
      </form>
    </Modal>
  )
}
