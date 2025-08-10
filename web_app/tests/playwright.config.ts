import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 60000,
  expect: {
    timeout: 10000
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [
    ['html'],
    ['line'],
    ['json', { outputFile: 'test-results.json' }]
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 15000,
    navigationTimeout: 30000,
  },

  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        // Capture console logs
        launchOptions: {
          args: ['--enable-logging'],
        }
      },
    },
    {
      name: 'debug',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        headless: false,
        video: 'on',
        screenshot: 'on',
        trace: 'on',
        launchOptions: {
          slowMo: 500,
          devtools: true,
        }
      },
    },
  ],

  // webServer: [
  //   {
  //     command: 'cd ../backend && python app.py',
  //     port: 8000,
  //     timeout: 120 * 1000,
  //     reuseExistingServer: true,
  //   },
  //   {
  //     command: 'cd ../frontend && npm run dev',
  //     port: 3000,
  //     timeout: 120 * 1000,
  //     reuseExistingServer: true,
  //   }
  // ],
});