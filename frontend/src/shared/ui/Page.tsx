import type { ReactNode } from 'react'

/** Slim full-width strip under the topbar: uppercase title left, actions right. */
export function PageHeader({ title, actions }: { title: string; actions?: ReactNode }) {
  return (
    <div className="bg-surface/60 border-line flex min-h-13 flex-wrap items-center justify-between gap-2 border-b px-4 py-2.5 sm:px-6">
      <h1 className="text-ink text-[13px] font-bold tracking-wide uppercase">{title}</h1>
      {actions ?? (
        <span className="text-ink-muted hidden items-center gap-1 text-xs md:flex">
          Vitals
          <i className="iconify tabler--chevron-right text-[10px]" aria-hidden />
          <span className="text-ink-faint">{title}</span>
        </span>
      )}
    </div>
  )
}

/** Content container below the page header. */
export function PageBody({ children }: { children: ReactNode }) {
  return <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6">{children}</div>
}

interface CardProps {
  title?: string
  actions?: ReactNode
  /** Skip the default body padding (for tables / divided lists). */
  flush?: boolean
  className?: string
  children: ReactNode
}

export function Card({ title, actions, flush = false, className = '', children }: CardProps) {
  return (
    <div
      className={`bg-surface border-line rounded-(--radius-card) border shadow-(--shadow-card) ${className}`}
    >
      {title !== undefined && (
        <div className="border-line flex flex-wrap items-center justify-between gap-2 border-b border-dashed px-5 py-3">
          <h2 className="text-ink text-sm font-semibold">{title}</h2>
          {actions}
        </div>
      )}
      <div className={flush ? '' : 'p-5'}>{children}</div>
    </div>
  )
}

export function EmptyState({ icon = 'tabler--inbox', message }: { icon?: string; message: string }) {
  return (
    <div className="border-line text-ink-muted flex flex-col items-center gap-2 rounded-(--radius-card) border border-dashed p-10 text-center text-sm">
      <i className={`iconify ${icon} text-ink-faint size-8`} aria-hidden />
      {message}
    </div>
  )
}

export function Spinner() {
  return (
    <div className="flex justify-center p-10">
      <div className="border-line border-t-primary h-6 w-6 animate-spin rounded-full border-2" />
    </div>
  )
}

export function ErrorNote({ error }: { error: unknown }) {
  let message = 'Something went wrong.'
  if (typeof error === 'object' && error !== null && 'data' in error) {
    const data = (error as { data: unknown }).data
    if (typeof data === 'object' && data !== null && 'detail' in data) {
      const detail = (data as { detail: unknown }).detail
      message = typeof detail === 'string' ? detail : JSON.stringify(detail)
    } else {
      message = JSON.stringify(data)
    }
  }
  return <div className="bg-accent-red/10 text-accent-red rounded-md p-3 text-sm">{message}</div>
}
