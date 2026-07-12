export type Role = 'admin' | 'clinician' | 'front_desk' | 'manager'

export interface User {
  id: string
  email: string
  displayName: string
  role: Role
  avatar: string | null
}

export interface AuthResponse {
  accessToken: string
  user: User
}

export interface Page<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export const roleLabels: Record<Role, string> = {
  admin: 'Administrator',
  clinician: 'Clinician',
  front_desk: 'Front desk',
  manager: 'Manager',
}
