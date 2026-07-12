import { request, type Page } from '@playwright/test'

export const PASSWORD = 'password123'

export const accounts = {
  admin: 'admin@vitals.test',
  clinician: 'chen@vitals.test',
  frontDesk: 'front@vitals.test',
  manager: 'manager@vitals.test',
}

/** Authenticate via the API and prime localStorage so pages load signed-in. */
export async function loginAs(page: Page, email: string) {
  const api = await request.newContext({ baseURL: 'http://localhost:8000' })
  const response = await api.post('/api/auth/login', {
    data: { email, password: PASSWORD },
  })
  if (!response.ok()) throw new Error(`Login failed for ${email}: ${response.status()}`)
  const auth = (await response.json()) as {
    accessToken: string
    user: { id: string; displayName: string }
  }
  await api.dispose()
  await page.addInitScript((state) => {
    localStorage.setItem('vitals-auth', JSON.stringify(state))
  }, { user: auth.user, accessToken: auth.accessToken })
  return auth
}

export function unique(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`
}
