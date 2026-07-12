import { useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react'

const controlClasses =
  'bg-surface border-line text-ink placeholder:text-ink-faint block h-9 w-full rounded-md border px-3 ' +
  'text-[13px] transition-colors focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20'

export function Label({ htmlFor, children }: { htmlFor?: string; children: ReactNode }) {
  return (
    <label htmlFor={htmlFor} className="text-ink mb-1.5 block text-[12.5px] font-semibold">
      {children}
    </label>
  )
}

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  /** Tabler icon class (e.g. "tabler--mail") rendered inside the field's left edge. */
  icon?: string
}

export function Input({ label, icon, className = '', id, ...rest }: InputProps) {
  const autoId = useId()
  const inputId = id ?? (label ? autoId : undefined)
  const input = icon ? (
    <div className="relative">
      <i
        className={`iconify ${icon} text-ink-faint pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2`}
        aria-hidden
      />
      <input id={inputId} className={`${controlClasses} pl-9 ${className}`} {...rest} />
    </div>
  ) : (
    <input id={inputId} className={`${controlClasses} ${className}`} {...rest} />
  )
  if (!label) return input
  return (
    <div>
      <Label htmlFor={inputId}>{label}</Label>
      {input}
    </div>
  )
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
}

export function Select({ label, className = '', children, id, ...rest }: SelectProps) {
  const autoId = useId()
  const selectId = id ?? (label ? autoId : undefined)
  const select = (
    <select id={selectId} className={`${controlClasses} appearance-none pr-8 ${className}`} {...rest}>
      {children}
    </select>
  )
  const wrapped = (
    <div className="relative">
      {select}
      <i
        className="iconify tabler--chevron-down text-ink-faint pointer-events-none absolute top-1/2 right-3 size-3.5 -translate-y-1/2"
        aria-hidden
      />
    </div>
  )
  if (!label) return wrapped
  return (
    <div>
      <Label htmlFor={selectId}>{label}</Label>
      {wrapped}
    </div>
  )
}

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
}

export function Textarea({ label, className = '', id, ...rest }: TextareaProps) {
  const autoId = useId()
  const textareaId = id ?? (label ? autoId : undefined)
  const textarea = (
    <textarea
      id={textareaId}
      className={`${controlClasses} h-auto min-h-20 resize-y py-2 ${className}`}
      {...rest}
    />
  )
  if (!label) return textarea
  return (
    <div>
      <Label htmlFor={textareaId}>{label}</Label>
      {textarea}
    </div>
  )
}
