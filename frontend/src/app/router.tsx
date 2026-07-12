import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from './Layout'
import { LoginPage, RegisterPage } from '../features/auth/AuthPages'
import { RouteError } from '../shared/ui/RouteError'
import { HomePage } from '../features/home/HomePage'

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
        children: [{ index: true, element: <HomePage /> }],
      },
    ],
  },
])
