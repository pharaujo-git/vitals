// Render docs/WRITEUP.md to docs/Vitals-Writeup.pdf with Playwright Chromium.
// Handles the markdown subset the writeup uses: headings, bold/italic/code,
// links, tables, and paragraphs.
import { chromium } from '@playwright/test'
import { readFileSync } from 'node:fs'

const DOCS = new URL('../../docs/', import.meta.url).pathname
const md = readFileSync(`${DOCS}WRITEUP.md`, 'utf8')

function inline(text) {
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2">$1</a>')
}

const blocks = md.split(/\n\n+/)
const html = blocks
  .map((block) => {
    const trimmed = block.trim()
    if (trimmed.startsWith('# ')) return `<h1>${inline(trimmed.slice(2))}</h1>`
    if (trimmed.startsWith('## ')) return `<h2>${inline(trimmed.slice(3))}</h2>`
    if (trimmed.startsWith('|')) {
      const rows = trimmed.split('\n').filter((row) => !/^\|[\s|:-]+\|$/.test(row))
      const [head, ...body] = rows.map((row) =>
        row.split('|').slice(1, -1).map((cell) => inline(cell.trim())),
      )
      return `<table><thead><tr>${head.map((c) => `<th>${c}</th>`).join('')}</tr></thead><tbody>${body
        .map((cells) => `<tr>${cells.map((c) => `<td>${c}</td>`).join('')}</tr>`)
        .join('')}</tbody></table>`
    }
    return `<p>${inline(trimmed.replace(/\n/g, ' '))}</p>`
  })
  .join('\n')

const page_html = `<!doctype html><html><head><meta charset="utf-8"><style>
  body { font: 10.5pt/1.5 Georgia, 'Times New Roman', serif; color: #1a1a1a;
         max-width: 46em; margin: 0 auto; }
  h1 { font-size: 15.5pt; line-height: 1.25; margin: 0 0 2pt; }
  h1 + p { color: #555; margin-top: 2pt; }
  h2 { font-size: 12pt; margin: 14pt 0 4pt; }
  p { margin: 6pt 0; text-align: justify; }
  code { font: 9pt ui-monospace, Menlo, monospace; background: #f2f2f2; padding: 0 2px; }
  a { color: #1a5276; text-decoration: none; }
  table { border-collapse: collapse; margin: 8pt auto; font-size: 9.5pt; }
  th, td { border: 0.5pt solid #999; padding: 3pt 8pt; text-align: center; }
  th { background: #f0f0f0; }
  td:first-child { text-align: left; }
</style></head><body>${html}</body></html>`

const browser = await chromium.launch()
const page = await browser.newPage()
await page.setContent(page_html, { waitUntil: 'load' })
await page.pdf({
  path: `${DOCS}Vitals-Writeup.pdf`,
  format: 'Letter',
  margin: { top: '0.9in', bottom: '0.9in', left: '1in', right: '1in' },
})
await browser.close()
console.log('wrote docs/Vitals-Writeup.pdf')
