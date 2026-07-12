interface Props {
  total: number
  limit: number
  offset: number
  onPage: (offset: number) => void
  /** Noun for the count line, e.g. "patient" → "12 patients". */
  noun?: string
}

/** Standard footer for paginated tables: count left, page controls right. */
export function Pagination({ total, limit, offset, onPage, noun = 'record' }: Props) {
  const page = Math.floor(offset / limit) + 1
  const totalPages = Math.max(Math.ceil(total / limit), 1)
  return (
    <div className="border-line text-ink-muted flex items-center justify-between border-t px-5 py-3 text-[13px]">
      <span>
        {total} {noun}
        {total === 1 ? '' : 's'}
      </span>
      <div className="flex items-center gap-3">
        <span>
          Page {page} of {totalPages}
        </span>
        <div className="flex -space-x-px">
          <button
            disabled={page <= 1}
            onClick={() => onPage(offset - limit)}
            className="border-line text-ink hover:bg-well flex size-8 items-center justify-center rounded-l-md border disabled:opacity-40"
            aria-label="Previous page"
          >
            <i className="iconify tabler--chevron-left size-4" aria-hidden />
          </button>
          <button
            disabled={page >= totalPages}
            onClick={() => onPage(offset + limit)}
            className="border-line text-ink hover:bg-well flex size-8 items-center justify-center rounded-r-md border disabled:opacity-40"
            aria-label="Next page"
          >
            <i className="iconify tabler--chevron-right size-4" aria-hidden />
          </button>
        </div>
      </div>
    </div>
  )
}
