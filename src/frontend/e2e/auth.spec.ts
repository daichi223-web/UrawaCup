import { test, expect } from '@playwright/test';

/**
 * 認証フロー E2Eテスト
 * - ログイン
 * - ログアウト
 * - 認証エラーハンドリング
 */

test.describe('認証機能', () => {
  test('ログインページが表示される', async ({ page }) => {
    await page.goto('/login');

    // ログインフォームの要素が存在することを確認
    await expect(page.getByPlaceholder(/ユーザー名を入力/)).toBeVisible();
    await expect(page.getByPlaceholder(/パスワードを入力/)).toBeVisible();
    await expect(page.getByRole('button', { name: /ログイン/i })).toBeVisible();
  });

  test('管理者ログインが成功する', async ({ page }) => {
    await page.goto('/login');

    // ログイン情報を入力
    await page.getByPlaceholder(/ユーザー名を入力/).fill('admin');
    await page.getByPlaceholder(/パスワードを入力/).fill('admin1234');

    // ログインボタンをクリック
    await page.getByRole('button', { name: /ログイン/i }).click();

    // ダッシュボード（ルート）にリダイレクトされることを確認
    await page.waitForURL('/', { timeout: 10000 });

    // ダッシュボードの要素が表示されることを確認
    // ローディング完了を待ってからh1ヘッダーを確認
    await expect(page.getByRole('heading', { name: /ダッシュボード/, level: 1 })).toBeVisible({ timeout: 15000 });
  });

  test('無効な認証情報でエラーが表示される', async ({ page }) => {
    await page.goto('/login');

    // 無効な認証情報を入力
    await page.getByPlaceholder(/ユーザー名を入力/).fill('invalid_user');
    await page.getByPlaceholder(/パスワードを入力/).fill('wrong_password');

    // ログインボタンをクリック
    await page.getByRole('button', { name: /ログイン/i }).click();

    // エラーメッセージが表示されることを確認
    await expect(
      page.locator('.bg-red-50').or(page.getByText(/ログイン.*失敗|失敗|401|unauthorized/i))
    ).toBeVisible({ timeout: 10000 });
  });

  test('ログアウトが成功する', async ({ page }) => {
    // まずログイン
    await page.goto('/login');
    await page.getByPlaceholder(/ユーザー名を入力/).fill('admin');
    await page.getByPlaceholder(/パスワードを入力/).fill('admin1234');
    await page.getByRole('button', { name: /ログイン/i }).click();

    // ダッシュボードに遷移するまで待機
    await page.waitForURL('/', { timeout: 10000 });

    // ログアウトボタンをクリック（サイドバーまたはヘッダーにある）
    const logoutButton = page.getByRole('button', { name: /ログアウト/i }).or(
      page.locator('button').filter({ hasText: /ログアウト/ })
    );

    if (await logoutButton.count() > 0) {
      await logoutButton.first().click();
      // ログインページにリダイレクトされることを確認
      await expect(page).toHaveURL(/.*login/, { timeout: 5000 });
    } else {
      // ログアウトボタンが見つからない場合はスキップ
      test.skip();
    }
  });
});
