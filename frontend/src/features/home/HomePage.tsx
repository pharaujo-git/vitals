import { Navigate } from 'react-router-dom'
import { useAppSelector } from '../../app/hooks'
import { DashboardPage } from '../dashboard/DashboardPage'

/** Role-aware landing: clinical staff go to patients, managers/admins get the dashboard. */
export function HomePage() {
  const user = useAppSelector((s) => s.auth.user)

  if (user && (user.role === 'clinician' || user.role === 'front_desk')) {
    return <Navigate to="/patients" replace />
  }

  return <DashboardPage />
}
