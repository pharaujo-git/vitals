import { useRef, useState, type FormEvent } from 'react'
import { useAppDispatch, useAppSelector } from '../../app/hooks'
import { roleLabels } from '../../shared/api/types'
import { Button } from '../../shared/ui/Button'
import { Input, Label } from '../../shared/ui/Field'
import { Card, ErrorNote, PageBody, PageHeader } from '../../shared/ui/Page'
import { useChangePasswordMutation, useUpdateProfileMutation } from '../auth/api'
import { updateUser } from '../auth/authSlice'

/** Downscale the picked image to a small square JPEG data URL so avatars
 *  stay well under the server's size cap. */
function fileToAvatar(file: File, size = 256): Promise<string> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const image = new Image()
    image.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = size
      canvas.height = size
      const context = canvas.getContext('2d')!
      // Cover-crop: scale the shorter side to `size`, center the other.
      const scale = size / Math.min(image.width, image.height)
      const width = image.width * scale
      const height = image.height * scale
      context.drawImage(image, (size - width) / 2, (size - height) / 2, width, height)
      URL.revokeObjectURL(url)
      resolve(canvas.toDataURL('image/jpeg', 0.85))
    }
    image.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Could not read the image'))
    }
    image.src = url
  })
}

function ProfileCard() {
  const user = useAppSelector((s) => s.auth.user)
  const dispatch = useAppDispatch()
  const [displayName, setDisplayName] = useState(user?.displayName ?? '')
  const [avatar, setAvatar] = useState<string | null>(user?.avatar ?? null)
  const fileRef = useRef<HTMLInputElement>(null)
  const [save, { isLoading, error }] = useUpdateProfileMutation()
  const [saved, setSaved] = useState(false)

  async function onPickPhoto(file: File | undefined) {
    if (!file) return
    setAvatar(await fileToAvatar(file))
    setSaved(false)
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const result = await save({ displayName, avatar })
    if ('data' in result && result.data) {
      dispatch(updateUser(result.data))
      setSaved(true)
    }
  }

  return (
    <Card title="Profile">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="flex items-center gap-4">
          {avatar ? (
            <img src={avatar} alt="Profile photo" className="size-20 rounded-full object-cover" />
          ) : (
            <span className="bg-primary/15 text-primary flex size-20 items-center justify-center rounded-full text-2xl font-bold">
              {user?.displayName.charAt(0).toUpperCase()}
            </span>
          )}
          <div className="space-y-1.5">
            <input
              ref={fileRef}
              type="file"
              accept="image/png,image/jpeg"
              className="hidden"
              onChange={(e) => onPickPhoto(e.target.files?.[0])}
            />
            <div className="flex gap-2">
              <Button type="button" variant="secondary" size="sm" onClick={() => fileRef.current?.click()}>
                <i className="iconify tabler--camera" aria-hidden /> Upload photo
              </Button>
              {avatar && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setAvatar(null)
                    setSaved(false)
                  }}
                >
                  Remove
                </Button>
              )}
            </div>
            <p className="text-ink-faint text-[11px]">
              PNG or JPEG; cropped to a square and resized automatically.
            </p>
          </div>
        </div>

        <Input
          label="Display name"
          required
          value={displayName}
          onChange={(e) => {
            setDisplayName(e.target.value)
            setSaved(false)
          }}
        />
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label>Email</Label>
            <p className="text-ink-muted bg-well truncate rounded-md px-3 py-2 text-[13px]">{user?.email}</p>
          </div>
          <div>
            <Label>Role</Label>
            <p className="text-ink-muted bg-well rounded-md px-3 py-2 text-[13px]">
              {user ? roleLabels[user.role] : ''}
            </p>
          </div>
        </div>
        {error !== undefined && <ErrorNote error={error} />}
        <div className="flex items-center justify-end gap-3">
          {saved && (
            <span className="text-accent-green text-[13px] font-semibold">
              <i className="iconify tabler--check align-[-2px]" aria-hidden /> Saved
            </span>
          )}
          <Button type="submit" disabled={isLoading}>
            Save profile
          </Button>
        </div>
      </form>
    </Card>
  )
}

function PasswordCard() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [change, { isLoading, error }] = useChangePasswordMutation()
  const [done, setDone] = useState(false)
  const mismatch = confirm !== '' && confirm !== newPassword

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (mismatch) return
    setDone(false) // hide any previous success note until THIS change lands
    const result = await change({ currentPassword, newPassword })
    if (!('error' in result)) {
      setCurrentPassword('')
      setNewPassword('')
      setConfirm('')
      setDone(true)
    }
  }

  return (
    <Card title="Password">
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Current password"
          type="password"
          required
          autoComplete="current-password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
        />
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
        {done && (
          <p className="text-accent-green text-[13px] font-semibold">
            Password changed. Other signed-in sessions were signed out.
          </p>
        )}
        <div className="flex justify-end">
          <Button type="submit" disabled={isLoading || mismatch}>
            Change password
          </Button>
        </div>
      </form>
    </Card>
  )
}

export function ProfilePage() {
  return (
    <>
      <PageHeader title="Profile" />
      <PageBody>
        <div className="grid items-start gap-4 lg:grid-cols-2">
          <ProfileCard />
          <PasswordCard />
        </div>
      </PageBody>
    </>
  )
}
