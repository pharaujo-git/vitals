// Capture README/docs screenshots from the running dev servers.
// Usage: node scripts/screenshots.mjs   (backend :8000 + vite :5173 + seeded DB)
import { chromium } from '@playwright/test'
import { mkdirSync } from 'node:fs'

const OUT = new URL('../../docs/screenshots/', import.meta.url).pathname
mkdirSync(OUT, { recursive: true })

async function login(email) {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password: 'password123' }),
  })
  if (!response.ok) throw new Error(`login failed for ${email}`)
  const auth = await response.json()
  return { user: auth.user, accessToken: auth.accessToken }
}

const browser = await chromium.launch()

async function shot({ email, path, file, theme = 'light', viewport = { width: 1440, height: 900 }, settle }) {
  const context = await browser.newContext({ viewport, deviceScaleFactor: 2 })
  const page = await context.newPage()
  const auth = email ? await login(email) : null
  await page.addInitScript(
    ([state, mode]) => {
      if (state) localStorage.setItem('vitals-auth', JSON.stringify(state))
      localStorage.setItem('vitals-theme', mode)
    },
    [auth, theme],
  )
  await page.goto(`http://localhost:5173${path}`)
  // 'networkidle' never fires (the app keeps SSE connections open); wait for UI.
  await page.waitForSelector('main', { timeout: 15000 })
  if (settle) await settle(page)
  await page.waitForTimeout(1200) // data fetches + chart animations
  await page.screenshot({ path: `${OUT}${file}` })
  await context.close()
  console.log(`captured ${file}`)
}

await shot({ email: 'manager@vitals.test', path: '/', file: 'dashboard-light.png' })
await shot({ email: 'manager@vitals.test', path: '/', file: 'dashboard-dark.png', theme: 'dark' })
await shot({
  email: 'chen@vitals.test',
  path: '/patients',
  file: 'patient-record.png',
  settle: async (page) => {
    await page.locator('tbody tr').first().click()
    await page.waitForSelector('text=Clinical lists')
  },
})
await shot({
  email: 'front@vitals.test',
  path: '/appointments',
  file: 'appointments-week.png',
  settle: async (page) => {
    await page.getByRole('button', { name: 'week' }).click()
    await page.waitForSelector('text=This week')
    await page.getByLabel('Clinician').selectOption({ label: 'Dr. Sarah Chen' })
  },
})
// Mobile sanity check of the week grid (scrolls inside its card).
await shot({
  email: 'front@vitals.test',
  path: '/appointments',
  file: 'mobile-week.png',
  viewport: { width: 390, height: 844 },
  settle: async (page) => {
    await page.getByRole('button', { name: 'week' }).click()
    await page.waitForSelector('text=This week')
  },
})

await browser.close()
