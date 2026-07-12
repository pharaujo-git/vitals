import { expect, test } from '@playwright/test'
import { accounts, loginAs, unique } from './helpers'

test('clinician creates a patient and finds them via search', async ({ page }) => {
  await loginAs(page, accounts.clinician)
  const lastName = unique('Testerson')

  await page.goto('/patients')
  await page.getByRole('button', { name: 'New patient' }).click()
  await page.getByLabel('First name').fill('Paula')
  await page.getByLabel('Last name').fill(lastName)
  await page.getByLabel('Date of birth').fill('1980-06-15')
  await page.getByLabel('Sex').selectOption('female')
  await page.getByLabel('Medical history').fill('Created by the e2e suite.')
  await page.getByRole('button', { name: 'Create' }).click()

  // Modal closes and the new patient is searchable.
  await page.getByPlaceholder('Search by name, identifier, phone or email…').fill(lastName)
  const row = page.getByRole('row', { name: new RegExp(lastName) })
  await expect(row).toBeVisible()

  // Open the record: demographics, clinical lists, timeline all render.
  await row.click()
  await expect(page.getByRole('heading', { name: `Paula ${lastName}` })).toBeVisible()
  await expect(page.getByText('Demographics')).toBeVisible()
  await expect(page.getByText('Clinical lists')).toBeVisible()
  await expect(page.getByText('Timeline')).toBeVisible()
  await expect(page.getByText('Created by the e2e suite.')).toBeVisible()
})

test('rejects a date of birth in the future', async ({ page }) => {
  await loginAs(page, accounts.clinician)
  await page.goto('/patients')
  await page.getByRole('button', { name: 'New patient' }).click()
  await page.getByLabel('First name').fill('Marty')
  await page.getByLabel('Last name').fill('McFly')
  await page.getByLabel('Date of birth').fill('2099-01-01')
  await page.getByRole('button', { name: 'Create' }).click()
  await expect(page.getByText('Date of birth cannot be in the future')).toBeVisible()
})
