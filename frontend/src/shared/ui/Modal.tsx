import type { ReactNode } from 'react'

interface Props {
  title: string
  open: boolean
  onClose: () => void
  wide?: boolean
  children: ReactNode
}

export function Modal({ title, open, onClose, wide = false, children }: Props) {
  if (!open) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        className={`bg-surface border-line max-h-[90vh] w-full overflow-y-auto rounded-lg border shadow-xl ${
          wide ? 'max-w-3xl' : 'max-w-lg'
        }`}
      >
        <div className="border-line flex items-center justify-between border-b px-5 py-3.5">
          <h2 className="text-ink text-[15px] font-semibold">{title}</h2>
          <button
            onClick={onClose}
            className="text-ink-muted hover:bg-well hover:text-ink flex size-7 items-center justify-center rounded-md"
            aria-label="Close"
          >
            <i className="iconify tabler--x text-base" aria-hidden />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  )
}
