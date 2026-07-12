import type { ButtonHTMLAttributes } from 'react'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'
type Size = 'md' | 'sm'

const variants: Record<Variant, string> = {
  primary: 'bg-primary text-white hover:bg-primary-deep disabled:opacity-60',
  secondary:
    'bg-surface text-ink border border-line hover:border-ink-faint hover:bg-well disabled:opacity-60',
  danger: 'bg-accent-red text-white hover:bg-accent-red/85 disabled:opacity-60',
  ghost: 'text-ink-muted hover:bg-well hover:text-ink disabled:opacity-60',
}

const sizes: Record<Size, string> = {
  md: 'px-3.5 py-2 text-[13px]',
  sm: 'px-2.5 py-1.5 text-xs',
}

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
}

export function Button({ variant = 'primary', size = 'md', className = '', ...rest }: Props) {
  return (
    <button
      className={`inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-md font-semibold transition-colors disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
      {...rest}
    />
  )
}
