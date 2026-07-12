import { Navigate } from 'react-router-dom'
import { useAppSelector } from '../../app/hooks'
import { Card, PageBody, PageHeader } from '../../shared/ui/Page'

/** Role-aware landing: clinical staff go straight to patients. */
export function HomePage() {
  const user = useAppSelector((s) => s.auth.user)

  if (user && (user.role === 'clinician' || user.role === 'front_desk')) {
    return <Navigate to="/patients" replace />
  }

  return (
    <>
      <PageHeader title="Home" />
      <PageBody>
        <Card>
          <p className="text-ink text-sm font-semibold">Welcome, {user?.displayName}.</p>
          <p className="text-ink-muted mt-1 text-[13px]">
            Vitals is ready. Features will appear in the sidebar as they come online.
          </p>
        </Card>
      </PageBody>
    </>
  )
}
