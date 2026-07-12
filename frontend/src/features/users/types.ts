import type { Role } from '../../shared/api/types'

export interface ManagedUser {
  id: string
  email: string
  displayName: string
  role: Role
  active: boolean
  createdAt: string
}
