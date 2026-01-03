import { defineConfig, devices } from '@playwright/test';

/**
 * 浦和カップ E2Eテスト設定
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  /* テストのタイムアウト設定 */
  timeout: 60000,
  expect: {
    timeout: 10000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  /*
   * 開発時は手動でサーバーを起動してください:
   * 1. バックエンド: cd src/backend && py -3 -m uvicorn main:app --port 8000
   * 2. フロントエンド: cd src/frontend && npm run dev
   *
   * CI環境では webServer を有効にすることを推奨
   */
});
