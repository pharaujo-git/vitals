import { expect, test } from '@playwright/test'
import { accounts, loginAs, unique } from './helpers'

test('clinician sends a message; front desk reads it and replies', async ({ browser }) => {
  const subject = unique('Coverage question')

  // Clinician composes a message to the front desk.
  const clinicianContext = await browser.newContext()
  const clinicianPage = await clinicianContext.newPage()
  await loginAs(clinicianPage, accounts.clinician)
  await clinicianPage.goto('/messages')
  await clinicianPage.getByRole('button', { name: 'New message' }).click()
  await clinicianPage.getByLabel('To', { exact: true }).selectOption({ label: 'Fran Alvarez — Front desk' })
  await clinicianPage.getByLabel('Subject').fill(subject)
  await clinicianPage.getByLabel('Message', { exact: true }).fill('Can you cover reception at noon?')
  await clinicianPage.getByRole('button', { name: 'Send' }).click()
  await clinicianPage.getByRole('button', { name: 'sent' }).click()
  await expect(clinicianPage.getByText(subject)).toBeVisible()

  // Front desk sees it unread, opens the thread, replies.
  const frontContext = await browser.newContext()
  const frontPage = await frontContext.newPage()
  await loginAs(frontPage, accounts.frontDesk)
  await frontPage.goto('/messages')
  await expect(frontPage.getByText(subject)).toBeVisible()
  await frontPage.getByText(subject).click()
  // Assert inside the thread modal — inbox previews may repeat the body text.
  const thread = frontPage.locator('.fixed.inset-0')
  await expect(thread.getByText('Can you cover reception at noon?')).toBeVisible()
  await thread.getByPlaceholder('Write a reply…').fill('Yes, no problem.')
  await thread.getByRole('button', { name: 'Reply' }).click()
  await expect(thread.getByText('Yes, no problem.')).toBeVisible()

  // The reply lands back in the clinician's inbox (reload — the write came
  // from another session, so the cached inbox can't know about it).
  await clinicianPage.goto('/messages')
  await clinicianPage.reload()
  await expect(clinicianPage.getByText(`Re: ${subject}`)).toBeVisible()

  await clinicianContext.close()
  await frontContext.close()
})
