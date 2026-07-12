import { useAppSelector } from '../../app/hooks'
import { Card, PageBody, PageHeader } from '../../shared/ui/Page'

export function HomePage() {
  const user = useAppSelector((s) => s.auth.user)
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
