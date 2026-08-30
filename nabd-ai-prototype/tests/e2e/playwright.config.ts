import { defineConfig, devices } from '@playwright/test';

/**
 * End-to-end configuration for the isolated synthetic prototype.
 *
 * These tests run against an already-running workbench (`make up`). They do not start or
 * seed the stack themselves, so a failing run never leaves a half-migrated database
 * behind, and they never reach any host other than the local workbench.
 */
export default defineConfig({
  testDir: './specs',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: '../../artifacts/e2e/report', open: 'never' }],
    ['json', { outputFile: '../../artifacts/e2e/results.json' }],
  ],
  timeout: 60_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
    actionTimeout: 15_000,
    // The prototype is local-only. Any request leaving the workbench is a defect, so the
    // context is given no proxy and no credentials.
    ignoreHTTPSErrors: false,
  },
  projects: [
    { name: 'chromium-ltr', use: { ...devices['Desktop Chrome'] } },
    {
      name: 'chromium-rtl',
      use: { ...devices['Desktop Chrome'], locale: 'ar', timezoneId: 'Asia/Dubai' },
    },
  ],
});
