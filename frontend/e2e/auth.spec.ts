import { expect, test } from '@playwright/test'
import { PASSWORD, accounts, unique } from './helpers'

test('login page shows dev demo accounts and one click fills the form', async ({ page }) => {
  await page.goto('/login')
  await expect(page.getByText('Demo accounts — dev only')).toBeVisible()
  await page.getByRole('button', { name: 'Clinician', exact: true }).click()
  await expect(page.getByLabel('Email')).toHaveValue(accounts.clinician)
  await page.getByRole('button', { name: 'Sign in' }).click()
  // Clinicians land on the patients list.
  await expect(page).toHaveURL(/\/patients/)
  await expect(page.getByRole('heading', { name: 'Patients' })).toBeVisible()
})

test('rejects wrong credentials with an inline error', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Email').fill(accounts.clinician)
  await page.getByLabel('Password').fill('not-the-password')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByText('Invalid email or password.')).toBeVisible()
  await expect(page).toHaveURL(/\/login/)
})

test('registers a new account with a role and signs in', async ({ page }) => {
  await page.goto('/register')
  await page.getByLabel('Name').fill('E2E Nurse')
  await page.getByLabel('Email').fill(`${unique('e2e')}@vitals.test`)
  await page.getByLabel('Role').selectOption('front_desk')
  await page.getByLabel('Password (min. 8 characters)').fill(PASSWORD)
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page).toHaveURL(/\/patients/)
})
