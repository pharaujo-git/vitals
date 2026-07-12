import { expect, test } from '@playwright/test'
import { accounts, loginAs, unique } from './helpers'

test('observation range validation rejects, then a valid encounter saves', async ({ page }) => {
  await loginAs(page, accounts.clinician)
  const reason = unique('Checkup')

  // Open the first patient in the list.
  await page.goto('/patients')
  await page.locator('tbody tr').first().click()
  await expect(page.getByText('Encounters')).toBeVisible()

  await page.getByRole('button', { name: 'New encounter' }).click()
  await page.getByLabel('Reason').fill(reason)
  // The default observation row is heart rate; 900 bpm is out of range.
  const valueInput = page.getByPlaceholder(/20–300/)
  await valueInput.fill('900')
  await page.getByRole('button', { name: 'Save encounter' }).click()
  await expect(page.getByText(/above the plausible range/)).toBeVisible()

  // Fix the value and save for real.
  await valueInput.fill('72')
  await page.getByRole('button', { name: 'Save encounter' }).click()
  await expect(page.getByText(/above the plausible range/)).toBeHidden()
  // The saved encounter shows up in both the encounter list and the timeline.
  await expect(page.getByText(new RegExp(reason)).first()).toBeVisible()
})
