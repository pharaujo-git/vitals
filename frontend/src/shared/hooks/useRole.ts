import { useAppSelector } from '../../app/hooks'
import type { Role } from '../api/types'

/** The signed-in user's role; RBAC gating on the client (the API enforces it regardless). */
export function useRole(): Role | null {
  return useAppSelector((s) => s.auth.user?.role ?? null)
}

export function useHasRole(...roles: Role[]): boolean {
  const role = useRole()
  return role !== null && (role === 'admin' || roles.includes(role))
}
