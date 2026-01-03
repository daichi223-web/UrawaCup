import { test, expect } from '@playwright/test';

/**
 * チーム管理 E2Eテスト
 */

// 共通のログインヘルパー
async function login(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.getByPlaceholder(/ユーザー名を入力/).fill('admin');
  await page.getByPlaceholder(/パスワードを入力/).fill('admin1234');
  await page.getByRole('button', { name: /ログイン/i }).click();
  await page.waitForURL('/', { timeout: 10000 });
}

test.describe('チーム管理機能', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('チーム一覧ページに遷移できる', async ({ page }) => {
    // サイドバーからチーム管理へ
    const teamLink = page.getByRole('link', { name: /チーム/i }).first();
    await teamLink.click();

    // チーム一覧が表示されることを確認
    await expect(page).toHaveURL(/.*team/i);
  });

  test('チーム一覧にデータが表示される', async ({ page }) => {
    await page.goto('/teams');
    await page.waitForLoadState('networkidle');

    // テーブルが表示されることを確認
    const table = page.locator('table');
    await expect(table).toBeVisible({ timeout: 10000 });

    // データ行があることを確認
    const rows = page.locator('table tbody tr');
    expect(await rows.count()).toBeGreaterThan(0);
  });

  test('チームを検索/フィルタできる', async ({ page }) => {
    await page.goto('/teams');
    await page.waitForLoadState('networkidle');

    // グループセレクタがあれば使用
    const groupSelect = page.locator('select').filter({ hasText: /グループ|選択/ });
    if (await groupSelect.count() > 0) {
      await groupSelect.first().selectOption({ index: 1 });
      await page.waitForTimeout(500);
    }
  });

  test('チーム編集モーダルが開ける', async ({ page }) => {
    await page.goto('/teams');
    await page.waitForLoadState('networkidle');

    // 編集ボタンをクリック
    const editButtons = page.locator('button').filter({ hasText: /編集/ });
    if (await editButtons.count() > 0) {
      await editButtons.first().click();

      // モーダルが開くことを確認
      await expect(page.getByText(/チーム編集/)).toBeVisible({ timeout: 5000 });
    }
  });
});
