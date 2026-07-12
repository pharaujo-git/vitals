import { Link, isRouteErrorResponse, useNavigate, useRouteError } from 'react-router-dom'
import { Button } from './Button'

/** Shared errorElement for all routes: 404s and page-render errors, with a way back. */
export function RouteError() {
  const error = useRouteError()
  const navigate = useNavigate()

  const is404 = isRouteErrorResponse(error) && error.status === 404
  const title = is404 ? 'Page not found' : 'Something went wrong'
  const message = is404
    ? 'The page you are looking for does not exist.'
    : error instanceof Error
      ? error.message
      : 'An unexpected error occurred while rendering this page.'

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <div className="max-w-md text-center">
        <span className="bg-accent-amber/20 text-accent-amber mx-auto flex size-12 items-center justify-center rounded-full">
          <i
            className={`iconify ${is404 ? 'tabler--map-question' : 'tabler--alert-triangle'} size-6`}
            aria-hidden
          />
        </span>
        <h1 className="text-ink mt-4 text-lg font-bold">{title}</h1>
        <p className="text-ink-muted mt-1 text-[13px]">{message}</p>
        <div className="mt-5 flex justify-center gap-2">
          <Button variant="secondary" onClick={() => navigate(-1)}>
            Go back
          </Button>
          <Link to="/">
            <Button>Home</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
