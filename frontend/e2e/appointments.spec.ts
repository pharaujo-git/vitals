import { expect, test } from '@playwright/test'
import { accounts, loginAs, unique } from './helpers'

test('front desk books, then cancels an appointment', async ({ page }) => {
  await loginAs(page, accounts.frontDesk)
  const reason = unique('E2E visit')

  await page.goto('/appointments')
  await page.getByRole('button', { name: 'Book appointment' }).click()

  // Scope to the modal — the page behind it has its own Clinician filter.
  const modal = page.locator('.fixed.inset-0')
  await modal.getByLabel('Patient').fill('a')
  // Pick the first matching patient; an early-morning slot dodges seeded overlaps.
  await modal.locator('select').first().selectOption({ index: 1 })
  await modal.getByLabel('Clinician').selectOption({ index: 1 })
  await modal.getByLabel('Start').fill('06:00')
  await modal.getByLabel('End').fill('06:20')
  await modal.getByLabel('Reason (optional)').fill(reason)
  await modal.getByRole('button', { name: 'Book', exact: true }).click()

  const row = page.getByRole('row', { name: new RegExp(reason) })
  await expect(row).toBeVisible()
  await expect(row.getByText('booked')).toBeVisible()

  // Cancel it via the row action + confirm dialog.
  await row.getByRole('button', { name: 'Cancel' }).click()
  await page.getByRole('button', { name: 'Cancel appointment' }).click()
  await expect(page.getByRole('row', { name: new RegExp(reason) }).getByText('cancelled')).toBeVisible()
})
