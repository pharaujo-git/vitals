import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAppDispatch } from '../../app/hooks'
import { Button } from '../../shared/ui/Button'
import { Input, Select } from '../../shared/ui/Field'
import { useLoginMutation, useRegisterMutation } from './api'
import { setCredentials } from './authSlice'

const features = [
  {
    icon: 'tabler--users',
    title: 'Patient records',
    text: 'Demographics, history and encounters in one reliable place',
  },
  {
    icon: 'tabler--calendar-time',
    title: 'Appointments',
    text: 'Booking, rescheduling and daily schedules per clinician',
  },
  {
    icon: 'tabler--heart-rate-monitor',
    title: 'Observations',
    text: 'Vital signs and notes captured during each encounter',
  },
  {
    icon: 'tabler--database-import',
    title: 'Data integration',
    text: 'CSV, HL7-style messages and FHIR merged into one store',
  },
  {
    icon: 'tabler--chart-histogram',
    title: 'Population health',
    text: 'Counts, trends and explainable patient risk flags',
  },
  {
    icon: 'tabler--shield-lock',
    title: 'Privacy',
    text: 'Role-based access, consent rules and a full audit trail',
  },
]

function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="bg-page flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-4xl">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          {/* App info panel — desktop only */}
          <div className="hidden lg:block">
            <div className="flex items-center gap-2.5">
              <span className="bg-primary shadow-primary/25 flex size-10 items-center justify-center rounded-xl text-white shadow-lg">
                <i className="iconify tabler--heartbeat text-xl" aria-hidden />
              </span>
              <span className="text-ink text-lg font-bold">Vitals</span>
            </div>
            <h2 className="text-ink mt-6 text-2xl font-bold">One consolidated view of every patient.</h2>
            <p className="text-ink-muted mt-2 max-w-md text-[13.5px]">
              A health information system with clinical data integration: records, appointments,
              observations and population analytics, all speaking FHIR.
            </p>
            <ul className="mt-7 grid grid-cols-1 gap-x-6 gap-y-5 xl:grid-cols-2">
              {features.map((f) => (
                <li key={f.title} className="flex items-start gap-3">
                  <span className="bg-primary/15 text-primary flex size-9 shrink-0 items-center justify-center rounded-full">
                    <i className={`iconify ${f.icon} size-4.5`} aria-hidden />
                  </span>
                  <div>
                    <p className="text-ink text-[13px] font-semibold">{f.title}</p>
                    <p className="text-ink-muted text-xs">{f.text}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          {/* Form column */}
          <div className="mx-auto w-full max-w-sm">
            <div className="mb-6 flex flex-col items-center text-center lg:hidden">
              <span className="bg-primary shadow-primary/25 flex size-12 items-center justify-center rounded-xl text-white shadow-lg">
                <i className="iconify tabler--heartbeat text-2xl" aria-hidden />
              </span>
              <h1 className="text-ink mt-4 text-lg font-bold">{title}</h1>
              <p className="text-ink-muted text-[13px]">{subtitle}</p>
            </div>
            <div className="bg-surface border-line rounded-xl border p-6 shadow-(--shadow-card) sm:p-7">
              <div className="mb-5 hidden lg:block">
                <h1 className="text-ink text-lg font-bold">{title}</h1>
                <p className="text-ink-muted text-[13px]">{subtitle}</p>
              </div>
              {children}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function errorMessage(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'status' in error) {
    const err = error as { status: number | string; data?: { detail?: unknown } }
    if (err.status === 401) return 'Invalid email or password.'
    if (typeof err.data?.detail === 'string') return err.data.detail
  }
  return 'Something went wrong. Is the API running?'
}

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [login, { isLoading, error }] = useLoginMutation()
  const dispatch = useAppDispatch()
  const navigate = useNavigate()

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const result = await login({ email, password })
    if ('data' in result && result.data) {
      dispatch(setCredentials(result.data))
      navigate('/')
    }
  }

  return (
    <AuthShell title="Welcome back" subtitle="Sign in to continue to Vitals">
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Email"
          icon="tabler--mail"
          type="email"
          required
          placeholder="you@clinic.org"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Input
          label="Password"
          icon="tabler--lock-password"
          type="password"
          required
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error !== undefined && <p className="text-accent-red text-[13px]">{errorMessage(error)}</p>}
        <Button type="submit" disabled={isLoading} className="w-full py-2.5">
          {isLoading ? 'Signing in…' : 'Sign in'}
        </Button>
        <p className="text-ink-muted text-center text-[13px]">
          New here?{' '}
          <Link to="/register" className="text-primary font-semibold underline-offset-4 hover:underline">
            Create an account
          </Link>
        </p>
      </form>
    </AuthShell>
  )
}

export function RegisterPage() {
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('clinician')
  const [register, { isLoading, error }] = useRegisterMutation()
  const dispatch = useAppDispatch()
  const navigate = useNavigate()

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const result = await register({ email, password, displayName, role })
    if ('data' in result && result.data) {
      dispatch(setCredentials(result.data))
      navigate('/')
    }
  }

  return (
    <AuthShell title="Create your account" subtitle="Set up access to the clinic system">
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Name"
          icon="tabler--user"
          required
          placeholder="Your name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
        />
        <Input
          label="Email"
          icon="tabler--mail"
          type="email"
          required
          placeholder="you@clinic.org"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Select label="Role" value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="clinician">Clinician</option>
          <option value="front_desk">Front desk</option>
          <option value="manager">Manager</option>
        </Select>
        <Input
          label="Password (min. 8 characters)"
          icon="tabler--lock-password"
          type="password"
          required
          minLength={8}
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error !== undefined && <p className="text-accent-red text-[13px]">{errorMessage(error)}</p>}
        <Button type="submit" disabled={isLoading} className="w-full py-2.5">
          {isLoading ? 'Creating account…' : 'Create account'}
        </Button>
        <p className="text-ink-muted text-center text-[13px]">
          Already registered?{' '}
          <Link to="/login" className="text-primary font-semibold underline-offset-4 hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </AuthShell>
  )
}
