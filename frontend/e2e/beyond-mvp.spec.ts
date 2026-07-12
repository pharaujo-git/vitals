import { expect, test } from '@playwright/test'
import { accounts, loginAs, unique } from './helpers'

// 1x1 transparent PNG
const PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
  'base64',
)

test('vitals trends render on a patient with observations', async ({ page }) => {
  await loginAs(page, accounts.clinician)
  await page.goto('/patients')
  await page.locator('tbody tr').first().click()
  await expect(page.getByText('Vitals trends')).toBeVisible()
})

test('imaging attachment uploads, previews and deletes', async ({ page }) => {
  await loginAs(page, accounts.clinician)
  const description = unique('Chest X-ray')

  await page.goto('/patients')
  await page.locator('tbody tr').first().click()
  await expect(page.getByText('Imaging & documents')).toBeVisible()

  // The patient-attachment picker is the only input accepting DICOM.
  await page.locator('input[accept*="dicom"]').setInputFiles({
    name: 'xray.png',
    mimeType: 'image/png',
    buffer: PNG,
  })
  await page.getByPlaceholder(/Description, e.g./).fill(description)
  await page.getByRole('button', { name: 'Upload' }).click()
  await expect(page.getByText(description)).toBeVisible()

  // Preview modal shows the image.
  await page.getByText(description).click()
  const modal = page.locator('.fixed.inset-0')
  await expect(modal.getByRole('img')).toBeVisible()
  await modal.getByRole('button', { name: 'Close' }).click()

  // Delete it again.
  await page.getByLabel('Delete attachment').first().click()
  await page.getByRole('button', { name: 'Delete', exact: true }).click()
  await expect(page.getByRole('button', { name: new RegExp(description) })).toBeHidden()
})

test('a message can be archived and restored', async ({ browser }) => {
  const subject = unique('Archive me')

  const senderContext = await browser.newContext()
  const senderPage = await senderContext.newPage()
  await loginAs(senderPage, accounts.manager)
  await senderPage.goto('/messages')
  await senderPage.getByRole('button', { name: 'New message' }).click()
  await senderPage.getByRole('checkbox', { name: /Fran Alvarez/ }).check()
  await senderPage.getByLabel('Subject').fill(subject)
  await senderPage.getByLabel('Message', { exact: true }).fill('File this away.')
  await senderPage.getByRole('button', { name: 'Send' }).click()
  await senderContext.close()

  const recipientContext = await browser.newContext()
  const recipientPage = await recipientContext.newPage()
  await loginAs(recipientPage, accounts.frontDesk)
  await recipientPage.goto('/messages')
  const row = recipientPage.locator('li').filter({ hasText: subject })
  await expect(row).toBeVisible()
  await row.getByLabel('Archive', { exact: true }).click()
  await expect(recipientPage.locator('li').filter({ hasText: subject })).toHaveCount(0)

  // It shows up under Archived and can be restored.
  await recipientPage.getByRole('button', { name: 'archived' }).click()
  const archivedRow = recipientPage.locator('li').filter({ hasText: subject })
  await expect(archivedRow).toBeVisible()
  await archivedRow.getByLabel('Move to inbox', { exact: true }).click()
  // Tab names may carry an unread-count badge, so anchor the match.
  await recipientPage.getByRole('button', { name: /^inbox/ }).click()
  await expect(recipientPage.locator('li').filter({ hasText: subject })).toBeVisible()
  await recipientContext.close()
})
