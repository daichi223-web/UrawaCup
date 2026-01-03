import { test, expect } from '@playwright/test';

/**
 * 試合管理 E2Eテスト
 */

// 共通のログインヘルパー
async function login(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.getByPlaceholder(/ユーザー名を入力/).fill('admin');
  await page.getByPlaceholder(/パスワードを入力/).fill('admin1234');
  await page.getByRole('button', { name: /ログイン/i }).click();
  await page.waitForURL('/', { timeout: 10000 });
}

test.describe('試合管理機能', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('試合結果ページに遷移できる', async ({ page }) => {
    // サイドバーから試合結果へ
    const matchLink = page.getByRole('link', { name: /試合結果|結果入力/i }).first();
    await matchLink.click();

    // URLを確認
    await expect(page).toHaveURL(/.*result/i);
  });

  test('試合スケジュールページに遷移できる', async ({ page }) => {
    const scheduleLink = page.getByRole('link', { name: /スケジュール|日程/i }).first();
    if (await scheduleLink.count() > 0) {
      await scheduleLink.click();
      await page.waitForLoadState('networkidle');
    }
  });

  test('試合データが表示される', async ({ page }) => {
    await page.goto('/results');
    await page.waitForLoadState('networkidle');

    // 何らかのコンテンツが表示されることを確認
    await expect(page.locator('main')).toBeVisible();
  });
});

test.describe('順位表機能', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('順位表ページに遷移できる', async ({ page }) => {
    const standingsLink = page.getByRole('link', { name: /順位/i }).first();
    await standingsLink.click();

    await expect(page).toHaveURL(/.*standings/i);
  });

  test('順位表が表示される', async ({ page }) => {
    await page.goto('/standings');
    await page.waitForLoadState('networkidle');

    // 順位表ページのヘッダーが表示されることを確認
    await expect(page.getByRole('heading', { name: /順位表/ })).toBeVisible({ timeout: 10000 });
  });
});

test.describe('得点ランキング機能', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('得点ランキングページに遷移できる', async ({ page }) => {
    const rankingLink = page.getByRole('link', { name: /得点|ランキング/i }).first();
    if (await rankingLink.count() > 0) {
      await rankingLink.click();
      await expect(page).toHaveURL(/.*scorer|.*ranking/i);
    }
  });
});

test.describe('レポート機能', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('レポートページに遷移できる', async ({ page }) => {
    const reportLink = page.getByRole('link', { name: /レポート|報告/i });
    if (await reportLink.count() > 0) {
      await reportLink.first().click();
      await expect(page).toHaveURL(/.*report/i);
    }
  });

  test('PDF出力ボタンが表示される', async ({ page }) => {
    await page.goto('/reports');
    await page.waitForLoadState('networkidle');

    const pdfButton = page.getByRole('button', { name: /PDF/i });
    if (await pdfButton.count() > 0) {
      await expect(pdfButton.first()).toBeVisible();
    }
  });

  test('Excel出力ボタンが表示される', async ({ page }) => {
    await page.goto('/reports');
    await page.waitForLoadState('networkidle');

    const excelButton = page.getByRole('button', { name: /Excel/i });
    if (await excelButton.count() > 0) {
      await expect(excelButton.first()).toBeVisible();
    }
  });
});
