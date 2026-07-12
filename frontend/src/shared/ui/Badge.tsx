import type { ReactNode } from 'react'

type Tone = 'primary' | 'blue' | 'green' | 'amber' | 'red' | 'violet' | 'muted'

const tones: Record<Tone, string> = {
  primary: 'bg-primary/15 text-primary',
  blue: 'bg-accent-blue/15 text-accent-blue',
  green: 'bg-accent-green/15 text-accent-green',
  amber: 'bg-accent-amber/20 text-accent-amber',
  red: 'bg-accent-red/15 text-accent-red',
  violet: 'bg-accent-violet/15 text-accent-violet',
  muted: 'bg-well text-ink-muted',
}

export function Badge({ tone = 'muted', children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-semibold ${tones[tone]}`}
    >
      {children}
    </span>
  )
}
