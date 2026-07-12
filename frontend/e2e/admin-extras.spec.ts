import { expect, test } from '@playwright/test'
import { PASSWORD, accounts, loginAs, unique } from './helpers'

test('forgot-password page acknowledges without confirming the account', async ({ page }) => {
  await page.goto('/login')
  await page.getByRole('link', { name: 'Forgot password?' }).click()
  await page.getByLabel('Email').fill('anyone@example.test')
  await page.getByRole('button', { name: 'Send reset link' }).click()
  await expect(page.getByText(/If an account exists/)).toBeVisible()
})

test('admin manages a user: role change, deactivate blocks login, reactivate', async ({ page, request }) => {
  // A disposable account to manage.
  const email = `${unique('managed')}@vitals.test`
  await request.post('http://localhost:8000/api/auth/register', {
    data: { email, password: PASSWORD, displayName: 'Managed User', role: 'front_desk' },
  })

  await loginAs(page, accounts.admin)
  await page.goto('/users')
  await page.getByPlaceholder('Search by name or email…').fill(email)
  const row = page.getByRole('row', { name: new RegExp(email) })
  await expect(row).toBeVisible()

  await row.getByLabel(/Role for/).selectOption('manager')
  await expect(row.getByLabel(/Role for/)).toHaveValue('manager')

  await row.getByRole('button', { name: 'Deactivate' }).click()
  await page.getByRole('button', { name: 'Deactivate', exact: true }).last().click()
  await expect(row.getByText('deactivated')).toBeVisible()

  const denied = await request.post('http://localhost:8000/api/auth/login', {
    data: { email, password: PASSWORD },
  })
  expect(denied.status()).toBe(401)

  await row.getByRole('button', { name: 'Reactivate' }).click()
  await expect(row.getByText('active', { exact: true })).toBeVisible()
})

test('appointments week grid renders with clinician blocks', async ({ page }) => {
  await loginAs(page, accounts.frontDesk)
  await page.goto('/appointments')
  await page.getByRole('button', { name: 'week' }).click()
  await expect(page.getByRole('button', { name: 'This week' })).toBeVisible()
  // Hour gutter and at least one appointment block from the seed.
  await expect(page.getByText('8:00', { exact: true })).toBeVisible()
  await expect(page.locator('[title*=":"]').first()).toBeVisible()
})

test('booking an appointment rings the clinician bell', async ({ browser }) => {
  const reason = unique('Bell test')

  // Front desk books the earliest free slot with Dr. Chen.
  const frontContext = await browser.newContext()
  const frontPage = await frontContext.newPage()
  await loginAs(frontPage, accounts.frontDesk)
  await frontPage.goto('/appointments')
  await frontPage.getByRole('button', { name: 'Book appointment' }).click()
  const modal = frontPage.locator('.fixed.inset-0')
  await modal.getByLabel('Patient').fill('a')
  await modal.locator('select').first().selectOption({ index: 1 })
  await modal.getByLabel('Clinician').selectOption({ label: 'Dr. Sarah Chen' })
  await modal.getByRole('button', { name: 'Find next free slot' }).click()
  await modal.getByLabel('Reason (optional)').fill(reason)
  await modal.getByRole('button', { name: 'Book', exact: true }).click()
  await expect(modal).toBeHidden()
  await frontContext.close()

  // Dr. Chen sees it in the notifications dropdown.
  const chenContext = await browser.newContext()
  const chenPage = await chenContext.newPage()
  await loginAs(chenPage, accounts.clinician)
  await chenPage.goto('/patients')
  await chenPage.getByLabel('Notifications').click()
  await expect(chenPage.getByText('New appointment booked').first()).toBeVisible()
  await chenContext.close()
})
