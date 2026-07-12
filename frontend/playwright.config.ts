import { defineConfig } from '@playwright/test'

// Runs against the dev servers (backend :8000, vite :5173) with the seeded
// database (backend/seed.py). Already-running servers are reused.
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  // Tests share one database, so keep them sequential and deterministic.
  workers: 1,
  fullyParallel: false,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: 'cd ../backend && .venv/bin/uvicorn app.main:app --port 8000',
      url: 'http://localhost:8000/api/health',
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
})
