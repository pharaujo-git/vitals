type Tone = 'primary' | 'blue' | 'green' | 'amber' | 'red'

const tones: Record<Tone, string> = {
  primary: 'bg-primary',
  blue: 'bg-accent-blue',
  green: 'bg-accent-green',
  amber: 'bg-accent-amber',
  red: 'bg-accent-red',
}

interface Props {
  /** 0..1 (clamped). */
  ratio: number
  tone?: Tone
  /** Explicit fill color — overrides tone. */
  color?: string
  className?: string
}

export function Progress({ ratio, tone = 'primary', color, className = 'h-1.5' }: Props) {
  const width = `${Math.min(Math.max(ratio, 0), 1) * 100}%`
  return (
    <div className={`bg-well w-full overflow-hidden rounded-full ${className}`}>
      <div
        className={`h-full rounded-full transition-all duration-500 ${color ? '' : tones[tone]}`}
        style={{ width, ...(color ? { backgroundColor: color } : {}) }}
      />
    </div>
  )
}
