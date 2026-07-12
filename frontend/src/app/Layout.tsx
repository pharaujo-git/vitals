import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from './hooks'
import { useLogoutMutation } from '../features/auth/api'
import { clearCredentials } from '../features/auth/authSlice'
import { useUnreadCountQuery } from '../features/messages/api'
import { SearchBox } from '../features/search/SearchBox'
import { baseApi } from '../shared/api/baseApi'
import { roleLabels, type Role } from '../shared/api/types'
import { useLiveUpdates } from '../shared/hooks/useLiveUpdates'
import { setTheme, useTheme } from '../shared/lib/theme'

interface NavItem {
  to: string
  label: string
  icon: string
  /** Roles that see this entry; admin always does. */
  roles: Role[]
}

const navItems: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: 'tabler--layout-dashboard', roles: ['manager'] },
  { to: '/patients', label: 'Patients', icon: 'tabler--users', roles: ['clinician', 'front_desk'] },
  {
    to: '/appointments',
    label: 'Appointments',
    icon: 'tabler--calendar-time',
    roles: ['clinician', 'front_desk'],
  },
  {
    to: '/messages',
    label: 'Messages',
    icon: 'tabler--mail',
    roles: ['clinician', 'front_desk', 'manager'],
  },
  { to: '/duplicates', label: 'Duplicates', icon: 'tabler--users-group', roles: ['clinician'] },
  { to: '/import', label: 'Import', icon: 'tabler--database-import', roles: [] },
  { to: '/reports', label: 'Reports', icon: 'tabler--report-analytics', roles: ['manager'] },
  { to: '/audit', label: 'Audit log', icon: 'tabler--shield-search', roles: [] },
]

export function AppLayout() {
  const user = useAppSelector((s) => s.auth.user)
  // One SSE connection for the whole shell: new mail invalidates Message caches.
  useLiveUpdates('messages', ['Message'])
  const [drawerOpen, setDrawerOpen] = useState(false)
  // Desktop-only: collapse the sidebar to an icon rail, persisted across reloads.
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('vitals-sidenav') === 'collapsed')
  const location = useLocation()

  // Close the mobile drawer whenever navigation happens.
  useEffect(() => setDrawerOpen(false), [location.pathname])

  if (!user) return <Navigate to="/login" replace />

  const visibleItems = navItems.filter(
    (item) => user.role === 'admin' || item.roles.includes(user.role),
  )

  function toggleNav() {
    if (window.matchMedia('(min-width: 1024px)').matches) {
      setCollapsed((v) => {
        localStorage.setItem('vitals-sidenav', v ? 'open' : 'collapsed')
        return !v
      })
    } else {
      setDrawerOpen((v) => !v)
    }
  }

  return (
    <div className="min-h-screen">
      {drawerOpen && (
        <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={() => setDrawerOpen(false)} />
      )}

      <aside
        className={`bg-sidenav fixed inset-y-0 z-40 flex w-60 flex-col transition-[width,transform] duration-200 lg:translate-x-0 ${
          collapsed ? 'lg:w-[68px]' : 'lg:w-60'
        } ${drawerOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div
          className={`border-sidenav-line flex h-16 items-center gap-2.5 border-b px-5 ${
            collapsed ? 'lg:justify-center lg:px-0' : ''
          }`}
        >
          <span className="bg-primary flex size-8 shrink-0 items-center justify-center rounded-lg text-white">
            <i className="iconify tabler--heartbeat text-lg" aria-hidden />
          </span>
          <span
            className={`text-sidenav-ink-bright text-[15px] font-bold tracking-wide ${
              collapsed ? 'lg:hidden' : ''
            }`}
          >
            Vitals
          </span>
        </div>

        <nav className="flex-1 overflow-x-hidden overflow-y-auto px-3 py-4">
          <p
            className={`text-sidenav-ink/60 mb-2 px-2.5 text-[10px] font-bold tracking-[0.14em] uppercase ${
              collapsed ? 'lg:hidden' : ''
            }`}
          >
            Navigation
          </p>
          <ul className="space-y-0.5">
            {visibleItems.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.to === '/'}
                  title={collapsed ? item.label : undefined}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-md px-2.5 py-2 text-[13.5px] font-medium transition-colors ${
                      collapsed ? 'lg:justify-center lg:px-0' : ''
                    } ${
                      isActive
                        ? 'bg-sidenav-active text-sidenav-ink-bright shadow-[inset_2px_0_0_0] shadow-primary'
                        : 'text-sidenav-ink hover:text-sidenav-ink-bright hover:bg-white/5'
                    }`
                  }
                >
                  <i className={`iconify ${item.icon} size-4.5 shrink-0`} aria-hidden />
                  <span className={collapsed ? 'lg:hidden' : ''}>{item.label}</span>
                  {item.to === '/messages' && <UnreadNavBadge collapsed={collapsed} />}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className={`border-sidenav-line border-t px-5 py-4 ${collapsed ? 'lg:px-2' : ''}`}>
          <div className={`flex items-center gap-2.5 ${collapsed ? 'lg:hidden' : ''}`}>
            <span className="text-sidenav-ink-bright flex size-8 shrink-0 items-center justify-center rounded-full bg-white/10 text-sm font-bold">
              {user.displayName.charAt(0).toUpperCase()}
            </span>
            <div className="min-w-0">
              <p className="text-sidenav-ink-bright truncate text-sm font-semibold">{user.displayName}</p>
              <p className="text-sidenav-ink truncate text-xs">{roleLabels[user.role]}</p>
            </div>
          </div>
          {collapsed && (
            <span
              title={user.displayName}
              className="text-sidenav-ink-bright mx-auto hidden size-8 items-center justify-center rounded-full bg-white/10 text-sm font-bold lg:flex"
            >
              {user.displayName.charAt(0).toUpperCase()}
            </span>
          )}
        </div>
      </aside>

      <div
        className={`flex min-h-screen flex-col transition-[padding] duration-200 ${
          collapsed ? 'lg:pl-[68px]' : 'lg:pl-60'
        }`}
      >
        <Topbar onToggleNav={toggleNav} />
        <main className="flex-1">
          <Outlet />
        </main>
        <footer className="border-line text-ink-muted border-t px-6 py-3 text-xs">
          Vitals — synthetic data only, no real patient information
        </footer>
      </div>
    </div>
  )
}

/** Unread-message count; refreshed by the SSE change signal, not polling. */
function UnreadNavBadge({ collapsed }: { collapsed: boolean }) {
  const { data } = useUnreadCountQuery()
  if (!data || data.count === 0) return null
  return (
    <span
      className={`bg-primary ml-auto rounded-full px-1.5 py-0.5 text-[10.5px] font-bold text-white ${
        collapsed ? 'lg:absolute lg:top-1 lg:right-1 lg:ml-0 lg:px-1 lg:py-0' : ''
      }`}
    >
      {data.count}
    </span>
  )
}

function TopbarMail() {
  const { data } = useUnreadCountQuery()
  return (
    <Link
      to="/messages"
      className="text-ink-muted hover:bg-well hover:text-ink relative flex size-9 items-center justify-center rounded-full transition-colors"
      aria-label="Messages"
    >
      <i className="iconify tabler--mail text-[19px]" aria-hidden />
      {(data?.count ?? 0) > 0 && (
        <span className="bg-primary absolute top-1 right-1 flex size-4 items-center justify-center rounded-full text-[9.5px] font-bold text-white">
          {data!.count > 9 ? '9+' : data!.count}
        </span>
      )}
    </Link>
  )
}

function Topbar({ onToggleNav }: { onToggleNav: () => void }) {
  const user = useAppSelector((s) => s.auth.user)
  const dispatch = useAppDispatch()
  const theme = useTheme()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!menuOpen) return
    function onClick(e: MouseEvent) {
      if (!menuRef.current?.contains(e.target as Node)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [menuOpen])

  const [serverLogout] = useLogoutMutation()

  function logout() {
    serverLogout() // revoke the refresh token + clear the cookie server-side
    dispatch(clearCredentials())
    dispatch(baseApi.util.resetApiState())
  }

  return (
    <header className="bg-surface border-line sticky top-0 z-20 flex h-16 items-center justify-between gap-3 border-b px-4 sm:px-6">
      <button
        onClick={onToggleNav}
        className="text-ink-muted hover:bg-well hover:text-ink flex size-9 shrink-0 items-center justify-center rounded-full"
        aria-label="Toggle menu"
      >
        <i className="iconify tabler--menu-2 text-xl" aria-hidden />
      </button>

      <div className="flex flex-1 justify-center px-2">
        <SearchBox />
      </div>

      <div className="flex items-center gap-1.5">
        <TopbarMail />
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          className="text-ink-muted hover:bg-well hover:text-ink flex size-9 items-center justify-center rounded-full transition-colors"
          aria-label="Toggle dark mode"
        >
          <i
            className={`iconify ${theme === 'dark' ? 'tabler--sun' : 'tabler--moon'} text-[19px]`}
            aria-hidden
          />
        </button>

        <div ref={menuRef} className="relative">
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="hover:bg-well flex items-center gap-2.5 rounded-full py-1.5 pr-2 pl-1.5 transition-colors"
          >
            <span className="bg-primary/15 text-primary flex size-8 items-center justify-center rounded-full text-sm font-bold">
              {user?.displayName.charAt(0).toUpperCase()}
            </span>
            <span className="text-ink hidden text-sm font-semibold sm:block">{user?.displayName}</span>
            <i className="iconify tabler--chevron-down text-ink-muted text-sm" aria-hidden />
          </button>
          {menuOpen && (
            <div className="bg-surface border-line absolute right-0 mt-1.5 w-52 rounded-lg border py-1.5 shadow-lg">
              <div className="border-line border-b px-4 pt-1 pb-2.5">
                <p className="text-ink truncate text-sm font-semibold">{user?.displayName}</p>
                <p className="text-ink-muted truncate text-xs">{user?.email}</p>
              </div>
              <button
                onClick={logout}
                className="text-accent-red hover:bg-well flex w-full items-center gap-2 px-4 py-2 text-sm font-medium"
              >
                <i className="iconify tabler--logout" aria-hidden />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
