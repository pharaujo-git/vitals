import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHasRole } from '../../shared/hooks/useRole'
import { formatDate, formatDateTime } from '../../shared/lib/format'
import { useGlobalSearchQuery } from './api'

/** Topbar quick search across patients and encounters (debounced). */
export function SearchBox() {
  const canSearch = useHasRole('clinician', 'front_desk')
  const [text, setText] = useState('')
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const boxRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  // Debounce keystrokes into the actual query.
  useEffect(() => {
    const handle = setTimeout(() => setQuery(text.trim()), 250)
    return () => clearTimeout(handle)
  }, [text])

  const { data, isFetching } = useGlobalSearchQuery(query, {
    skip: !canSearch || query.length < 2,
  })

  useEffect(() => {
    if (!open) return
    function onClick(e: MouseEvent) {
      if (!boxRef.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  if (!canSearch) return null

  const showResults = open && query.length >= 2
  const hasHits = (data?.patients.length ?? 0) + (data?.encounters.length ?? 0) > 0

  function go(patientId: string) {
    setOpen(false)
    setText('')
    navigate(`/patients/${patientId}`)
  }

  return (
    <div ref={boxRef} className="relative w-full max-w-md">
      <i
        className="iconify tabler--search text-ink-faint pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2"
        aria-hidden
      />
      <input
        placeholder="Search patients, identifiers, encounters…"
        value={text}
        onFocus={() => setOpen(true)}
        onChange={(e) => {
          setText(e.target.value)
          setOpen(true)
        }}
        className="bg-well border-line text-ink placeholder:text-ink-faint focus:border-primary focus:ring-primary/20 h-9 w-full rounded-full border pr-4 pl-9 text-[13px] transition-colors focus:ring-2 focus:outline-none"
      />
      {showResults && (
        <div className="bg-surface border-line absolute top-11 right-0 left-0 z-30 max-h-96 overflow-y-auto rounded-lg border py-2 shadow-lg">
          {isFetching && <p className="text-ink-muted px-4 py-2 text-xs">Searching…</p>}
          {!isFetching && !hasHits && (
            <p className="text-ink-muted px-4 py-2 text-xs">No matches for “{query}”.</p>
          )}
          {data && data.patients.length > 0 && (
            <>
              <p className="text-ink-faint px-4 pt-1 pb-1.5 text-[10px] font-bold tracking-[0.12em] uppercase">
                Patients
              </p>
              {data.patients.map((p) => (
                <button
                  key={p.id}
                  onClick={() => go(p.id)}
                  className="hover:bg-well flex w-full items-center gap-3 px-4 py-2 text-left"
                >
                  <i className="iconify tabler--user text-ink-faint size-4 shrink-0" aria-hidden />
                  <span className="text-ink min-w-0 flex-1 truncate text-[13px] font-medium">
                    {p.lastName}, {p.firstName}
                  </span>
                  <span className="text-ink-muted font-mono text-xs">{p.mrn}</span>
                  <span className="text-ink-faint text-xs">{formatDate(p.dob)}</span>
                </button>
              ))}
            </>
          )}
          {data && data.encounters.length > 0 && (
            <>
              <p className="text-ink-faint px-4 pt-2 pb-1.5 text-[10px] font-bold tracking-[0.12em] uppercase">
                Encounters
              </p>
              {data.encounters.map((e) => (
                <button
                  key={e.id}
                  onClick={() => go(e.patientId)}
                  className="hover:bg-well flex w-full items-center gap-3 px-4 py-2 text-left"
                >
                  <i
                    className="iconify tabler--stethoscope text-ink-faint size-4 shrink-0"
                    aria-hidden
                  />
                  <span className="text-ink min-w-0 flex-1 truncate text-[13px]">
                    {e.reason ?? 'Encounter'}
                    <span className="text-ink-muted"> — {e.patientName}</span>
                  </span>
                  <span className="text-ink-faint text-xs whitespace-nowrap">
                    {formatDateTime(e.occurredAt)}
                  </span>
                </button>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  )
}
