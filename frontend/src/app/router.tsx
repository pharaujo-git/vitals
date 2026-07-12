import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from './Layout'
import { LoginPage, RegisterPage } from '../features/auth/AuthPages'
import { RouteError } from '../shared/ui/RouteError'
import { HomePage } from '../features/home/HomePage'
import { PatientsPage } from '../features/patients/PatientsPage'
import { PatientDetailPage } from '../features/patients/PatientDetailPage'
import { AppointmentsPage } from '../features/appointments/AppointmentsPage'
import { AuditPage } from '../features/audit/AuditPage'
import { ImportPage } from '../features/import/ImportPage'
import { DuplicatesPage } from '../features/duplicates/DuplicatesPage'
import { ReportsPage } from '../features/reports/ReportsPage'

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage />, errorElement: <RouteError /> },
  { path: '/register', element: <RegisterPage />, errorElement: <RouteError /> },
  {
    path: '/',
    element: <AppLayout />,
    errorElement: <RouteError />,
    children: [
      // Pathless child so page-level errors render inside the layout chrome.
      {
        errorElement: <RouteError />,
        children: [
          { index: true, element: <HomePage /> },
          { path: 'patients', element: <PatientsPage /> },
          { path: 'patients/:id', element: <PatientDetailPage /> },
          { path: 'appointments', element: <AppointmentsPage /> },
          { path: 'audit', element: <AuditPage /> },
          { path: 'import', element: <ImportPage /> },
          { path: 'duplicates', element: <DuplicatesPage /> },
          { path: 'reports', element: <ReportsPage /> },
        ],
      },
    ],
  },
])
