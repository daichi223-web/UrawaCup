"""
浦和カップ トーナメント管理システム - 網羅的E2Eテスト
全ページを巡回し、コンソールエラーを検出する
"""

import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, expect

# テスト設定
BASE_URL = "http://localhost:5175"
API_URL = "http://localhost:8000/api"

# テスト対象ページ
PAGES = {
    "public": [
        {"path": "/public/matches", "name": "パブリック試合一覧", "auth": False},
        {"path": "/public/standings", "name": "パブリック順位表", "auth": False},
    ],
    "authenticated": [
        {"path": "/", "name": "ダッシュボード", "auth": True},
        {"path": "/standings", "name": "順位表", "auth": True},
        {"path": "/scorer-ranking", "name": "得点ランキング", "auth": True},
        {"path": "/teams", "name": "チーム管理", "auth": True, "admin": True},
        {"path": "/schedule", "name": "日程管理", "auth": True, "admin": True},
        {"path": "/results", "name": "試合結果入力", "auth": True},
        {"path": "/reports", "name": "報告書出力", "auth": True, "admin": True},
        {"path": "/approval", "name": "結果承認", "auth": True, "admin": True},
        {"path": "/settings", "name": "設定", "auth": True, "admin": True},
        {"path": "/exclusions", "name": "対戦除外設定", "auth": True, "admin": True},
    ],
}

class E2ETestRunner:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.tested_pages = []

    def log_error(self, page_name, path, error_type, message):
        self.errors.append({
            "page": page_name,
            "path": path,
            "type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        })
        print(f"[ERROR] {page_name} ({path}): {error_type} - {message}")

    def log_warning(self, page_name, path, message):
        self.warnings.append({
            "page": page_name,
            "path": path,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        })
        print(f"[WARN] {page_name} ({path}): {message}")

    def log_success(self, page_name, path):
        self.tested_pages.append({
            "page": page_name,
            "path": path,
            "status": "OK",
            "timestamp": datetime.now().isoformat(),
        })
        print(f"[OK] {page_name} ({path})")

    def run_tests(self):
        print("=" * 60)
        print("浦和カップ E2Eテスト開始")
        print("=" * 60)

        with sync_playwright() as p:
            # Chromiumでテスト
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # コンソールエラーをキャプチャ
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
            page.on("pageerror", lambda err: console_errors.append(err))

            # 1. パブリックページのテスト（認証不要）
            print("\n--- パブリックページのテスト ---")
            for page_info in PAGES["public"]:
                console_errors.clear()
                self._test_page(page, page_info, console_errors)

            # 2. 認証ページのテスト
            print("\n--- 認証ページのテスト ---")

            # まずログインを試行
            print("\nログイン処理...")
            login_success = self._try_login(page, console_errors)

            if login_success:
                for page_info in PAGES["authenticated"]:
                    console_errors.clear()
                    self._test_page(page, page_info, console_errors)
            else:
                print("[WARN] ログインできなかったため、認証ページのテストをスキップ")
                # ログインなしでもアクセスできるページをテスト
                for page_info in PAGES["authenticated"]:
                    if not page_info.get("admin"):
                        console_errors.clear()
                        self._test_page(page, page_info, console_errors)

            browser.close()

        # レポート生成
        self._generate_report()

    def _test_page(self, page, page_info, console_errors):
        path = page_info["path"]
        name = page_info["name"]

        try:
            # ページにアクセス
            response = page.goto(f"{BASE_URL}{path}", wait_until="networkidle", timeout=30000)

            # HTTPステータスチェック
            if response and response.status >= 400:
                self.log_error(name, path, "HTTP Error", f"Status: {response.status}")
                return

            # ページ読み込み待機
            time.sleep(2)

            # コンソールエラーチェック
            for err in console_errors:
                if hasattr(err, 'text'):
                    error_text = err.text
                else:
                    error_text = str(err)

                # 重要なエラーをフィルタリング
                if any(keyword in error_text.lower() for keyword in
                       ['error', 'uncaught', 'failed', 'invalid', 'undefined', 'null']):
                    self.log_error(name, path, "Console Error", error_text[:200])

            # 画面上のエラー表示をチェック
            error_elements = page.locator(".error, .alert-danger, [class*='error']").all()
            for elem in error_elements:
                if elem.is_visible():
                    text = elem.text_content()
                    if text and len(text.strip()) > 0:
                        self.log_warning(name, path, f"UI Error: {text[:100]}")

            # React Error Boundaryチェック
            error_boundary = page.locator("text=Something went wrong").first
            if error_boundary.is_visible():
                self.log_error(name, path, "React Error Boundary", "Component crash detected")
                return

            # 成功
            if not any(e["path"] == path for e in self.errors):
                self.log_success(name, path)

        except Exception as e:
            self.log_error(name, path, "Test Exception", str(e)[:200])

    def _try_login(self, page, console_errors):
        """ログイン処理を試行"""
        try:
            page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=30000)
            time.sleep(1)

            # ログインフォームがあるか確認
            username_field = page.locator("input[name='username'], input[type='text']").first
            password_field = page.locator("input[name='password'], input[type='password']").first

            if username_field.is_visible() and password_field.is_visible():
                username_field.fill("admin")
                password_field.fill("admin1234")

                # ログインボタンをクリック
                submit_btn = page.locator("button[type='submit'], button:has-text('ログイン')").first
                if submit_btn.is_visible():
                    submit_btn.click()
                    time.sleep(2)

                    # ログイン成功確認（ダッシュボードにリダイレクトされるか）
                    if "/login" not in page.url:
                        print("[OK] ログイン成功")
                        return True
                    else:
                        print("[WARN] ログイン失敗（認証情報が正しくない可能性）")
                        return False
            else:
                print("[WARN] ログインフォームが見つかりません")
                return False

        except Exception as e:
            print(f"[ERROR] ログイン処理中にエラー: {e}")
            return False

    def _generate_report(self):
        """テスト結果レポートを生成"""
        print("\n" + "=" * 60)
        print("テスト結果サマリー")
        print("=" * 60)

        total_pages = len(self.tested_pages) + len(self.errors)
        success_count = len([p for p in self.tested_pages if p["status"] == "OK"])
        error_count = len(self.errors)
        warning_count = len(self.warnings)

        print(f"テストページ数: {total_pages}")
        print(f"成功: {success_count}")
        print(f"エラー: {error_count}")
        print(f"警告: {warning_count}")

        if self.errors:
            print("\n--- 検出されたエラー ---")
            for err in self.errors:
                print(f"  [{err['type']}] {err['page']} ({err['path']})")
                print(f"    {err['message']}")

        if self.warnings:
            print("\n--- 警告 ---")
            for warn in self.warnings:
                print(f"  {warn['page']} ({warn['path']}): {warn['message']}")

        # JSON形式でも保存
        report = {
            "test_date": datetime.now().isoformat(),
            "summary": {
                "total_pages": total_pages,
                "success": success_count,
                "errors": error_count,
                "warnings": warning_count,
            },
            "tested_pages": self.tested_pages,
            "errors": self.errors,
            "warnings": self.warnings,
        }

        with open("D:/UrawaCup/tests/e2e_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n詳細レポート: D:/UrawaCup/tests/e2e_report.json")

        return report


if __name__ == "__main__":
    runner = E2ETestRunner()
    runner.run_tests()
