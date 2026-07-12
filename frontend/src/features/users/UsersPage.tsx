import { useState } from 'react'
import { useAppSelector } from '../../app/hooks'
import { usePagination } from '../../shared/hooks/usePagination'
import { roleLabels, type Role } from '../../shared/api/types'
import { formatDate } from '../../shared/lib/format'
import { Badge } from '../../shared/ui/Badge'
import { Button } from '../../shared/ui/Button'
import { ConfirmDialog } from '../../shared/ui/ConfirmDialog'
import { Input, Select } from '../../shared/ui/Field'
import { Modal } from '../../shared/ui/Modal'
import { Card, EmptyState, PageBody, PageHeader, Spinner } from '../../shared/ui/Page'
import { Pagination } from '../../shared/ui/Pagination'
import {
  useAdminResetPasswordMutation,
  useSetUserActiveMutation,
  useSetUserRoleMutation,
  useUsersQuery,
} from './api'
import type { ManagedUser } from './types'

const ROLES: Role[] = ['admin', 'clinician', 'front_desk', 'manager']

export function UsersPage() {
  const me = useAppSelector((s) => s.auth.user)
  const [search, setSearch] = useState('')
  const { limit, offset, setPage, reset } = usePagination()
  const { data, isLoading, isFetching } = useUsersQuery({ search: search || undefined, limit, offset })
  const [setRole] = useSetUserRoleMutation()
  const [setActive, { isLoading: toggling }] = useSetUserActiveMutation()
  const [resetPassword, { isLoading: resetting }] = useAdminResetPasswordMutation()
  const [deactivating, setDeactivating] = useState<ManagedUser | null>(null)
  const [tempPassword, setTempPassword] = useState<{ user: ManagedUser; password: string } | null>(null)

  async function onResetPassword(user: ManagedUser) {
    const result = await resetPassword(user.id)
    if ('data' in result && result.data) {
      setTempPassword({ user, password: result.data.tempPassword })
    }
  }

  return (
    <>
      <PageHeader title="Users" />
      <PageBody>
        <Card className="mb-4">
          <Input
            icon="tabler--search"
            placeholder="Search by name or email…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              reset()
            }}
          />
        </Card>

        {isLoading && <Spinner />}
        {data && data.items.length === 0 && (
          <EmptyState icon="tabler--user-off" message="No users match." />
        )}
        {data && data.items.length > 0 && (
          <Card flush className={isFetching ? 'opacity-60' : ''}>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="bg-well text-ink-muted border-line border-b text-left text-[10.5px] font-bold tracking-[0.08em] uppercase">
                    <th className="px-5 py-2.5">User</th>
                    <th className="px-5 py-2.5">Role</th>
                    <th className="px-5 py-2.5">Status</th>
                    <th className="px-5 py-2.5">Joined</th>
                    <th className="px-2 py-2.5" />
                  </tr>
                </thead>
                <tbody className="divide-line divide-y">
                  {data.items.map((user) => {
                    const isSelf = user.id === me?.id
                    return (
                      <tr key={user.id} className={`hover:bg-well/60 transition-colors ${user.active ? '' : 'opacity-60'}`}>
                        <td className="px-5 py-2.5">
                          <span className="text-ink font-medium">
                            {user.displayName}
                            {isSelf && <span className="text-ink-faint ml-1.5 text-xs">(you)</span>}
                          </span>
                          <span className="text-ink-muted block text-xs">{user.email}</span>
                        </td>
                        <td className="px-5 py-2.5">
                          <div className="w-36">
                            <Select
                              value={user.role}
                              disabled={isSelf}
                              onChange={(e) => setRole({ id: user.id, role: e.target.value })}
                              aria-label={`Role for ${user.displayName}`}
                            >
                              {ROLES.map((role) => (
                                <option key={role} value={role}>
                                  {roleLabels[role]}
                                </option>
                              ))}
                            </Select>
                          </div>
                        </td>
                        <td className="px-5 py-2.5">
                          <Badge tone={user.active ? 'green' : 'red'}>
                            {user.active ? 'active' : 'deactivated'}
                          </Badge>
                        </td>
                        <td className="text-ink-muted px-5 py-2.5 whitespace-nowrap">
                          {formatDate(user.createdAt)}
                        </td>
                        <td className="px-2 py-2.5 whitespace-nowrap">
                          {!isSelf && (
                            <div className="flex justify-end gap-1.5">
                              <Button
                                size="sm"
                                variant="secondary"
                                disabled={resetting}
                                onClick={() => onResetPassword(user)}
                              >
                                <i className="iconify tabler--key" aria-hidden /> Reset password
                              </Button>
                              {user.active ? (
                                <Button size="sm" variant="danger" onClick={() => setDeactivating(user)}>
                                  Deactivate
                                </Button>
                              ) : (
                                <Button
                                  size="sm"
                                  disabled={toggling}
                                  onClick={() => setActive({ id: user.id, active: true })}
                                >
                                  Reactivate
                                </Button>
                              )}
                            </div>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <Pagination total={data.total} limit={limit} offset={offset} onPage={setPage} noun="user" />
          </Card>
        )}

        {deactivating && (
          <ConfirmDialog
            open
            title="Deactivate account"
            message={`Deactivate ${deactivating.displayName}? They are signed out everywhere immediately and cannot sign in; their historical records stay attributed to them.`}
            confirmLabel="Deactivate"
            busy={toggling}
            onConfirm={async () => {
              await setActive({ id: deactivating.id, active: false })
              setDeactivating(null)
            }}
            onClose={() => setDeactivating(null)}
          />
        )}

        {tempPassword && (
          <Modal title="Temporary password" open onClose={() => setTempPassword(null)}>
            <p className="text-ink-muted text-[13px]">
              {tempPassword.user.displayName} was signed out everywhere. Share this temporary
              password with them securely — it is shown only once:
            </p>
            <p className="bg-well text-ink mt-3 rounded-md p-3 text-center font-mono text-lg font-bold select-all">
              {tempPassword.password}
            </p>
            <p className="text-ink-faint mt-2 text-xs">
              They should change it right away on their profile page.
            </p>
            <div className="mt-4 flex justify-end">
              <Button onClick={() => setTempPassword(null)}>Done</Button>
            </div>
          </Modal>
        )}
      </PageBody>
    </>
  )
}
