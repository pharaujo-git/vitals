import type { ReactNode } from 'react'
import { Button } from './Button'

interface Props {
  open: boolean
  title: string
  message: ReactNode
  confirmLabel?: string
  busy?: boolean
  onConfirm: () => void
  onClose: () => void
}

/** In-app replacement for window.confirm, styled like the rest of the UI. */
export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Delete',
  busy = false,
  onConfirm,
  onClose,
}: Props) {
  if (!open) return null
  return (
    <div
      className="fixed inset-0 z-60 flex items-center justify-center bg-black/50 p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="bg-surface border-line w-full max-w-sm rounded-lg border p-5 shadow-xl">
        <div className="flex items-start gap-3.5">
          <span className="bg-accent-red/15 text-accent-red flex size-10 shrink-0 items-center justify-center rounded-full">
            <i className="iconify tabler--alert-triangle size-5" aria-hidden />
          </span>
          <div className="min-w-0">
            <h2 className="text-ink text-[15px] font-semibold">{title}</h2>
            <p className="text-ink-muted mt-1 text-[13px]">{message}</p>
          </div>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button variant="danger" onClick={onConfirm} disabled={busy}>
            {busy ? 'Working…' : confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
