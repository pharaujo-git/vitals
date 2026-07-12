import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

/** Last-resort catch for errors outside the router (providers, the router itself). */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  render() {
    if (this.state.error === null) return this.props.children
    return (
      <div className="bg-page flex min-h-screen items-center justify-center p-4">
        <div className="bg-surface border-line w-full max-w-md rounded-lg border p-6 text-center shadow-(--shadow-card)">
          <span className="bg-accent-red/15 text-accent-red mx-auto flex size-12 items-center justify-center rounded-full">
            <i className="iconify tabler--alert-triangle size-6" aria-hidden />
          </span>
          <h1 className="text-ink mt-4 text-lg font-bold">Something went wrong</h1>
          <p className="text-ink-muted mt-1 text-[13px]">{this.state.error.message}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-primary hover:bg-primary-deep mt-5 rounded-md px-4 py-2 text-[13px] font-semibold text-white"
          >
            Reload
          </button>
        </div>
      </div>
    )
  }
}
