import { expect, test } from '@playwright/test'
import { accounts, loginAs } from './helpers'

test('manager lands on the dashboard with population data and no patient nav', async ({ page }) => {
  await loginAs(page, accounts.manager)
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Population dashboard' })).toBeVisible()
  await expect(page.getByText('Encounters per month')).toBeVisible()
  await expect(page.getByText('Risk flags')).toBeVisible()
  const nav = page.getByRole('navigation')
  await expect(nav.getByText('Reports')).toBeVisible()
  await expect(nav.getByText('Patients')).toHaveCount(0)
  await expect(nav.getByText('Import')).toHaveCount(0)
})

test('front desk sees patients and appointments but no clinical/admin areas', async ({ page }) => {
  await loginAs(page, accounts.frontDesk)
  await page.goto('/')
  await expect(page).toHaveURL(/\/patients/)
  const nav = page.getByRole('navigation')
  await expect(nav.getByText('Appointments')).toBeVisible()
  await expect(nav.getByText('Messages')).toBeVisible()
  await expect(nav.getByText('Duplicates')).toHaveCount(0)
  await expect(nav.getByText('Audit log')).toHaveCount(0)
  // Opening a patient shows demographics but no clinical cards.
  await page.locator('tbody tr').first().click()
  await expect(page.getByText('Demographics')).toBeVisible()
  await expect(page.getByText('Clinical lists')).toHaveCount(0)
  await expect(page.getByText('Encounters', { exact: true })).toHaveCount(0)
})

test('admin can browse the audit log with recorded actions', async ({ page }) => {
  await loginAs(page, accounts.admin)
  await page.goto('/audit')
  await expect(page.getByRole('heading', { name: 'Audit log' })).toBeVisible()
  await expect(page.locator('tbody tr').first()).toBeVisible()
})

test('manager reports preview is de-identified', async ({ page }) => {
  await loginAs(page, accounts.manager)
  await page.goto('/reports')
  await expect(page.getByText(/De-identified export/)).toBeVisible()
  // No Patient (name) column for managers.
  await expect(page.locator('thead').getByText('Patient')).toHaveCount(0)
  await expect(page.locator('tbody tr').first()).toBeVisible()
})
