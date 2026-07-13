import { expect, test } from '@playwright/test'
import { accounts, loginAs } from './helpers'

test('sign out everywhere ends the other session too', async ({ browser }) => {
  // Two independent signed-in sessions for the same account.
  const deviceA = await browser.newContext()
  const pageA = await deviceA.newPage()
  await loginAs(pageA, accounts.manager)
  await pageA.goto('/reports')
  await expect(pageA.getByRole('heading', { name: 'Cohort reports' })).toBeVisible()

  const deviceB = await browser.newContext()
  const pageB = await deviceB.newPage()
  await loginAs(pageB, accounts.manager)

  // Wait past a second so device A's token second precedes the cutoff second.
  await pageB.waitForTimeout(1100)

  // Device B signs out everywhere from the profile page.
  await pageB.goto('/profile')
  await pageB.getByRole('button', { name: 'Sign out everywhere' }).click()
  await pageB.getByRole('button', { name: 'Sign out everywhere', exact: true }).last().click()
  await expect(pageB).toHaveURL(/\/login/)

  // Device A is dead on its next interaction: the API rejects its token,
  // the cookie-less refresh fails, and the app drops to the login page.
  await pageA.reload()
  await expect(pageA).toHaveURL(/\/login/)

  await deviceA.close()
  await deviceB.close()
})
