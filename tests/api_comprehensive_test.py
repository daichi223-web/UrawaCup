"""
浦和カップ トーナメント管理システム - 網羅的APIテスト
全APIエンドポイントを呼び出し、レスポンス形式を検証する
"""

import json
import httpx
from datetime import datetime

# テスト設定
API_URL = "http://localhost:8000/api"
FRONTEND_URL = "http://localhost:5175"

class APITestRunner:
    def __init__(self):
        self.client = httpx.Client(base_url=API_URL, timeout=30.0)
        self.errors = []
        self.warnings = []
        self.successes = []
        self.token = None

    def log_error(self, endpoint, error_type, message, details=None):
        entry = {
            "endpoint": endpoint,
            "type": error_type,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.errors.append(entry)
        print(f"[ERROR] {endpoint}: {error_type} - {message}")
        if details:
            print(f"        Details: {details}")

    def log_warning(self, endpoint, message, details=None):
        entry = {
            "endpoint": endpoint,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.warnings.append(entry)
        print(f"[WARN] {endpoint}: {message}")

    def log_success(self, endpoint, message="OK"):
        entry = {
            "endpoint": endpoint,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.successes.append(entry)
        print(f"[OK] {endpoint}: {message}")

    def run_tests(self):
        print("=" * 60)
        print("浦和カップ APIテスト開始")
        print("=" * 60)

        # 1. ヘルスチェック
        self.test_health()

        # 2. 認証テスト
        self.test_auth()

        # 3. トーナメントAPIテスト
        self.test_tournaments()

        # 4. チームAPIテスト
        self.test_teams()

        # 5. 会場APIテスト
        self.test_venues()

        # 6. 試合APIテスト
        self.test_matches()

        # 7. 順位APIテスト
        self.test_standings()

        # 8. レスポンス形式の検証（snake_case vs camelCase）
        self.test_response_format()

        # レポート生成
        self._generate_report()

    def test_health(self):
        print("\n--- ヘルスチェック ---")
        try:
            resp = self.client.get("/health", follow_redirects=True)
            # /health は /api 外かもしれないので直接アクセス
            resp2 = httpx.get("http://localhost:8000/health", timeout=10.0)
            if resp2.status_code == 200:
                self.log_success("/health", "サーバー稼働中")
            else:
                self.log_error("/health", "HTTP Error", f"Status: {resp2.status_code}")
        except Exception as e:
            self.log_error("/health", "Connection Error", str(e))

    def test_auth(self):
        print("\n--- 認証APIテスト ---")

        # ログイン試行
        try:
            resp = self.client.post("/auth/login", json={
                "username": "admin",
                "password": "admin1234"
            })

            if resp.status_code == 200:
                data = resp.json()
                # snake_case vs camelCase チェック
                if "access_token" in data:
                    self.token = data["access_token"]
                    self.log_warning("/auth/login", "snake_case 'access_token' を使用（camelCase推奨）")
                elif "accessToken" in data:
                    self.token = data["accessToken"]
                    self.log_success("/auth/login", "ログイン成功 (camelCase)")
                else:
                    self.log_error("/auth/login", "Format Error", "access_token が見つからない", data)

                # ユーザー情報のフォーマットチェック
                self._check_camel_case("LoginResponse", data)
            else:
                self.log_warning("/auth/login", f"ログイン失敗 (Status: {resp.status_code}) - 管理者未作成の可能性")
        except Exception as e:
            self.log_error("/auth/login", "Request Error", str(e))

    def test_tournaments(self):
        print("\n--- トーナメントAPIテスト ---")

        try:
            resp = self.client.get("/tournaments")
            if resp.status_code == 200:
                data = resp.json()
                self.log_success("/tournaments", f"取得成功 (total: {data.get('total', 'N/A')})")

                # フォーマットチェック
                if "tournaments" in data and len(data["tournaments"]) > 0:
                    tournament = data["tournaments"][0]
                    self._check_camel_case("Tournament", tournament)

                    # 特にstartDate/start_dateをチェック
                    if "start_date" in tournament and "startDate" not in tournament:
                        self.log_error("/tournaments", "snake_case Issue",
                            "start_date がsnake_caseのまま（Issue #018関連）",
                            {"found": "start_date", "expected": "startDate"})
                    elif "startDate" in tournament:
                        self.log_success("/tournaments", "startDate は camelCase で正常")
            else:
                self.log_error("/tournaments", "HTTP Error", f"Status: {resp.status_code}")
        except Exception as e:
            self.log_error("/tournaments", "Request Error", str(e))

        # 個別トーナメント取得
        try:
            resp = self.client.get("/tournaments/1")
            if resp.status_code == 200:
                data = resp.json()
                self._check_camel_case("Tournament[1]", data)

                # start_date/startDateの詳細チェック
                if "start_date" in data:
                    self.log_error("/tournaments/1", "snake_case Issue",
                        "start_date がsnake_caseのまま（MatchSchedule.tsxでInvalid time valueエラーの原因）",
                        {"actual_key": "start_date", "value": data.get("start_date")})
                elif "startDate" in data:
                    self.log_success("/tournaments/1", f"startDate={data.get('startDate')} (camelCase OK)")
            elif resp.status_code == 404:
                self.log_warning("/tournaments/1", "トーナメントが存在しない")
        except Exception as e:
            self.log_error("/tournaments/1", "Request Error", str(e))

    def test_teams(self):
        print("\n--- チームAPIテスト ---")

        try:
            resp = self.client.get("/teams?tournament_id=1")
            if resp.status_code == 200:
                data = resp.json()
                self.log_success("/teams", f"取得成功 (total: {data.get('total', 'N/A')})")

                if "teams" in data and len(data["teams"]) > 0:
                    team = data["teams"][0]
                    self._check_camel_case("Team", team)
            elif resp.status_code == 404:
                self.log_warning("/teams", "チームが存在しない")
            else:
                self.log_error("/teams", "HTTP Error", f"Status: {resp.status_code}")
        except Exception as e:
            self.log_error("/teams", "Request Error", str(e))

    def test_venues(self):
        print("\n--- 会場APIテスト ---")

        try:
            resp = self.client.get("/venues?tournament_id=1")
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    self.log_success("/venues", f"取得成功 ({len(data)}件)")
                    if len(data) > 0:
                        self._check_camel_case("Venue", data[0])
                else:
                    self.log_success("/venues", "取得成功")
            else:
                self.log_warning("/venues", f"Status: {resp.status_code}")
        except Exception as e:
            self.log_error("/venues", "Request Error", str(e))

    def test_matches(self):
        print("\n--- 試合APIテスト ---")

        try:
            resp = self.client.get("/matches?tournament_id=1&limit=10")
            if resp.status_code == 200:
                data = resp.json()
                self.log_success("/matches", f"取得成功 (total: {data.get('total', 'N/A')})")

                if "matches" in data and len(data["matches"]) > 0:
                    match = data["matches"][0]
                    self._check_camel_case("Match", match)

                    # 特に日時フィールドをチェック
                    date_fields = ["match_date", "matchDate", "match_time", "matchTime"]
                    found_fields = [f for f in date_fields if f in match]
                    snake_fields = [f for f in found_fields if "_" in f]
                    if snake_fields:
                        self.log_warning("/matches", f"snake_caseフィールド検出: {snake_fields}")
            else:
                self.log_warning("/matches", f"Status: {resp.status_code}")
        except Exception as e:
            self.log_error("/matches", "Request Error", str(e))

    def test_standings(self):
        print("\n--- 順位APIテスト ---")

        try:
            resp = self.client.get("/standings/1")
            if resp.status_code == 200:
                data = resp.json()
                self.log_success("/standings/1", "取得成功")

                if isinstance(data, list) and len(data) > 0:
                    self._check_camel_case("Standing", data[0])
            elif resp.status_code == 404:
                self.log_warning("/standings/1", "順位データが存在しない")
            else:
                self.log_warning("/standings/1", f"Status: {resp.status_code}")
        except Exception as e:
            self.log_error("/standings/1", "Request Error", str(e))

        # 得点ランキング
        try:
            resp = self.client.get("/standings/1/top-scorers")
            if resp.status_code == 200:
                self.log_success("/standings/1/top-scorers", "取得成功")
            elif resp.status_code == 404:
                self.log_warning("/standings/1/top-scorers", "データなし")
        except Exception as e:
            self.log_error("/standings/1/top-scorers", "Request Error", str(e))

    def test_response_format(self):
        print("\n--- レスポンス形式の総合検証 ---")

        # 各エンドポイントのレスポンスを収集してsnake_caseの使用をチェック
        endpoints_to_check = [
            "/tournaments",
            "/tournaments/1",
            "/teams?tournament_id=1",
            "/venues?tournament_id=1",
            "/matches?tournament_id=1&limit=5",
        ]

        snake_case_fields_found = []

        for endpoint in endpoints_to_check:
            try:
                resp = self.client.get(endpoint)
                if resp.status_code == 200:
                    data = resp.json()
                    snake_fields = self._find_snake_case_fields(data)
                    if snake_fields:
                        snake_case_fields_found.append({
                            "endpoint": endpoint,
                            "fields": snake_fields
                        })
            except:
                pass

        if snake_case_fields_found:
            print("\n[SUMMARY] snake_caseフィールドが検出されました:")
            for item in snake_case_fields_found:
                print(f"  {item['endpoint']}: {', '.join(item['fields'][:5])}")
                if len(item['fields']) > 5:
                    print(f"    ...他 {len(item['fields']) - 5} フィールド")

    def _check_camel_case(self, context, obj):
        """オブジェクトのキーがcamelCaseかどうかチェック"""
        if not isinstance(obj, dict):
            return

        snake_case_keys = [k for k in obj.keys() if "_" in k and not k.startswith("_")]
        if snake_case_keys:
            self.log_warning(context, f"snake_caseキー検出: {snake_case_keys[:5]}")

    def _find_snake_case_fields(self, data, prefix=""):
        """再帰的にsnake_caseフィールドを探す"""
        fields = []

        if isinstance(data, dict):
            for key, value in data.items():
                if "_" in key and not key.startswith("_"):
                    fields.append(f"{prefix}{key}")
                fields.extend(self._find_snake_case_fields(value, f"{prefix}{key}."))
        elif isinstance(data, list) and len(data) > 0:
            fields.extend(self._find_snake_case_fields(data[0], f"{prefix}[0]."))

        return fields

    def _generate_report(self):
        """テスト結果レポートを生成"""
        print("\n" + "=" * 60)
        print("テスト結果サマリー")
        print("=" * 60)

        print(f"成功: {len(self.successes)}")
        print(f"エラー: {len(self.errors)}")
        print(f"警告: {len(self.warnings)}")

        if self.errors:
            print("\n--- 検出されたエラー ---")
            for err in self.errors:
                print(f"  [{err['type']}] {err['endpoint']}")
                print(f"    {err['message']}")
                if err.get('details'):
                    print(f"    Details: {err['details']}")

        if self.warnings:
            print("\n--- 警告 ---")
            for warn in self.warnings:
                print(f"  {warn['endpoint']}: {warn['message']}")

        # JSON形式でも保存
        report = {
            "test_date": datetime.now().isoformat(),
            "summary": {
                "success": len(self.successes),
                "errors": len(self.errors),
                "warnings": len(self.warnings),
            },
            "successes": self.successes,
            "errors": self.errors,
            "warnings": self.warnings,
        }

        with open("D:/UrawaCup/tests/api_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n詳細レポート: D:/UrawaCup/tests/api_test_report.json")

        return report


if __name__ == "__main__":
    runner = APITestRunner()
    runner.run_tests()
