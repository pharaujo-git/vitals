import { expect, test } from '@playwright/test'
import { PASSWORD, accounts, loginAs, unique } from './helpers'

const PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
  'base64',
)

test('profile updates name and photo, visible in the topbar', async ({ page }) => {
  await loginAs(page, accounts.manager)
  const name = unique('Mia')

  await page.goto('/profile')
  await page.getByLabel('Display name').fill(name)
  await page.locator('input[type="file"]').setInputFiles({
    name: 'me.png',
    mimeType: 'image/png',
    buffer: PNG,
  })
  await page.getByRole('button', { name: 'Save profile' }).click()
  await expect(page.getByText('Saved')).toBeVisible()

  // The shell reflects the change without a reload.
  await expect(page.locator('header').getByText(name)).toBeVisible()
  await expect(page.locator('header img[src^="data:image/jpeg"]')).toBeVisible()

  // Restore the seeded name so reruns stay stable.
  await page.getByLabel('Display name').fill('Mia Manager')
  await page.getByRole('button', { name: 'Save profile' }).click()
  await expect(page.getByText('Saved')).toBeVisible()
})

test('password change requires the current password, then round-trips', async ({ page }) => {
  await loginAs(page, accounts.manager)
  await page.goto('/profile')

  await page.getByLabel('Current password').fill('not-right')
  await page.getByLabel('New password (min. 8 characters)').fill('temporary-pass-1')
  await page.getByLabel('Confirm new password').fill('temporary-pass-1')
  await page.getByRole('button', { name: 'Change password' }).click()
  await expect(page.getByText('Current password is incorrect')).toBeVisible()

  await page.getByLabel('Current password').fill(PASSWORD)
  await page.getByRole('button', { name: 'Change password' }).click()
  await expect(page.getByText(/Password changed/)).toBeVisible()

  // Change it straight back so the demo credentials keep working.
  await page.getByLabel('Current password').fill('temporary-pass-1')
  await page.getByLabel('New password (min. 8 characters)').fill(PASSWORD)
  await page.getByLabel('Confirm new password').fill(PASSWORD)
  await page.getByRole('button', { name: 'Change password' }).click()
  await expect(page.getByText(/Password changed/)).toBeVisible()
})
