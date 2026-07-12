import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Button } from '../../shared/ui/Button'
import { Input } from '../../shared/ui/Field'
import { ErrorNote } from '../../shared/ui/Page'
import { useForgotPasswordMutation, useResetPasswordMutation } from './api'

function NarrowShell({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="bg-page flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center text-center">
          <span className="bg-primary shadow-primary/25 flex size-12 items-center justify-center rounded-xl text-white shadow-lg">
            <i className="iconify tabler--heartbeat text-2xl" aria-hidden />
          </span>
          <h1 className="text-ink mt-4 text-lg font-bold">{title}</h1>
          <p className="text-ink-muted text-[13px]">{subtitle}</p>
        </div>
        <div className="bg-surface border-line rounded-xl border p-6 shadow-(--shadow-card) sm:p-7">
          {children}
        </div>
      </div>
    </div>
  )
}

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [request, { isLoading }] = useForgotPasswordMutation()

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    await request({ email })
    setSent(true) // always — the server never confirms whether the email exists
  }

  return (
    <NarrowShell title="Forgot your password?" subtitle="We'll issue a reset link for your account">
      {sent ? (
        <div className="space-y-4 text-center">
          <i className="iconify tabler--mail-forward text-primary size-10" aria-hidden />
          <p className="text-ink text-[13px]">
            If an account exists for <span className="font-semibold">{email}</span>, a reset link
            has been issued.
          </p>
          <p className="text-ink-faint text-xs">
            Dev environment: the link is printed to the backend server log instead of being
            emailed.
          </p>
          <Link to="/login" className="text-primary block text-[13px] font-semibold hover:underline">
            Back to sign in
          </Link>
        </div>
      ) : (
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
          <Button type="submit" disabled={isLoading} className="w-full py-2.5">
            {isLoading ? 'Requesting…' : 'Send reset link'}
          </Button>
          <p className="text-ink-muted text-center text-[13px]">
            Remembered it?{' '}
            <Link to="/login" className="text-primary font-semibold underline-offset-4 hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      )}
    </NarrowShell>
  )
}

export function ResetPasswordPage() {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [reset, { isLoading, error }] = useResetPasswordMutation()
  const [done, setDone] = useState(false)
  const navigate = useNavigate()
  const mismatch = confirm !== '' && confirm !== newPassword

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (mismatch) return
    const result = await reset({ token, newPassword })
    if (!('error' in result)) {
      setDone(true)
      setTimeout(() => navigate('/login'), 1800)
    }
  }

  return (
    <NarrowShell title="Choose a new password" subtitle="Your other sessions will be signed out">
      {done ? (
        <div className="space-y-3 text-center">
          <i className="iconify tabler--circle-check text-accent-green size-10" aria-hidden />
          <p className="text-ink text-[13px] font-semibold">Password updated — sending you to sign in…</p>
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4">
          {!token && (
            <ErrorNote error={{ data: { detail: 'Missing reset token — use the full link from the reset message.' } }} />
          )}
          <Input
            label="New password (min. 8 characters)"
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <Input
            label="Confirm new password"
            type="password"
            required
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
          />
          {mismatch && <p className="text-accent-red text-[13px]">Passwords do not match.</p>}
          {error !== undefined && <ErrorNote error={error} />}
          <Button type="submit" disabled={isLoading || mismatch || !token} className="w-full py-2.5">
            {isLoading ? 'Saving…' : 'Set new password'}
          </Button>
        </form>
      )}
    </NarrowShell>
  )
}
