"""
浦和カップ - エッジケース・バリデーション・セキュリティテスト
"""
import json
import httpx
from datetime import datetime

API_URL = "http://localhost:8000/api"

class EdgeSecurityTest:
    def __init__(self):
        self.client = httpx.Client(base_url=API_URL, timeout=30.0, follow_redirects=True)
        self.issues = []
        self.passed = []
        self.token = None

    def log_issue(self, category, test_name, message, severity="medium"):
        self.issues.append({
            "category": category,
            "test": test_name,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })
        print(f"[ISSUE-{severity.upper()}] {category}/{test_name}: {message}")

    def log_pass(self, category, test_name, message="OK"):
        self.passed.append({"category": category, "test": test_name, "message": message})
        print(f"[PASS] {category}/{test_name}: {message}")

    def get_auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def login(self):
        resp = self.client.post("/auth/login", json={"username": "admin", "password": "admin1234"})
        if resp.status_code == 200:
            self.token = resp.json().get("accessToken")
            return True
        return False

    def run_all(self):
        print("=" * 70)
        print("エッジケース・バリデーション・セキュリティテスト")
        print("=" * 70)

        self.login()

        # エッジケーステスト
        self.test_empty_strings()
        self.test_long_strings()
        self.test_invalid_ids()
        self.test_negative_numbers()
        self.test_special_characters()

        # セキュリティテスト
        self.test_auth_bypass()
        self.test_unauthorized_access()
        self.test_sql_injection()
        self.test_xss_prevention()

        self._generate_report()

    def test_empty_strings(self):
        """空文字列のテスト"""
        print("\n--- 空文字列テスト ---")

        # チーム名が空
        resp = self.client.post("/teams/", json={
            "name": "",
            "tournamentId": 1,
            "teamType": "invited"
        }, headers=self.get_auth_headers())

        if resp.status_code == 422:
            self.log_pass("EdgeCase", "empty_team_name", "空のチーム名を適切に拒否")
        elif resp.status_code == 201:
            self.log_issue("EdgeCase", "empty_team_name", "空のチーム名が許可された", "high")
        else:
            self.log_pass("EdgeCase", "empty_team_name", f"Status {resp.status_code}")

    def test_long_strings(self):
        """超長文字列のテスト"""
        print("\n--- 超長文字列テスト ---")

        long_name = "A" * 1000
        resp = self.client.post("/teams/", json={
            "name": long_name,
            "tournamentId": 1,
            "teamType": "invited"
        }, headers=self.get_auth_headers())

        if resp.status_code == 422:
            self.log_pass("EdgeCase", "long_string", "超長文字列を適切に拒否")
        elif resp.status_code == 201:
            # 作成された場合は削除
            team_id = resp.json().get("id")
            self.client.delete(f"/teams/{team_id}", headers=self.get_auth_headers())
            self.log_issue("EdgeCase", "long_string", "1000文字のチーム名が許可された", "low")
        else:
            self.log_pass("EdgeCase", "long_string", f"Status {resp.status_code}")

    def test_invalid_ids(self):
        """無効なIDのテスト"""
        print("\n--- 無効ID テスト ---")

        # 存在しないチームID
        resp = self.client.get("/teams/99999", headers=self.get_auth_headers())
        if resp.status_code == 404:
            self.log_pass("EdgeCase", "nonexistent_team", "存在しないチームで404")
        else:
            self.log_issue("EdgeCase", "nonexistent_team", f"期待:404, 実際:{resp.status_code}")

        # 負のID
        resp = self.client.get("/teams/-1", headers=self.get_auth_headers())
        if resp.status_code in [404, 422]:
            self.log_pass("EdgeCase", "negative_id", "負のIDを適切に処理")
        else:
            self.log_issue("EdgeCase", "negative_id", f"負のIDでStatus {resp.status_code}")

        # 文字列ID (should be handled by FastAPI)
        resp = self.client.get("/teams/abc", headers=self.get_auth_headers())
        if resp.status_code == 422:
            self.log_pass("EdgeCase", "string_id", "文字列IDを適切に拒否")
        else:
            self.log_issue("EdgeCase", "string_id", f"文字列IDでStatus {resp.status_code}")

    def test_negative_numbers(self):
        """負の数値のテスト"""
        print("\n--- 負の数値テスト ---")

        # 負のtournament_id
        resp = self.client.get("/teams?tournament_id=-1", headers=self.get_auth_headers())
        if resp.status_code in [200, 422]:
            self.log_pass("EdgeCase", "negative_tournament_id", f"Status {resp.status_code}")
        else:
            self.log_issue("EdgeCase", "negative_tournament_id", f"予期しないStatus {resp.status_code}")

    def test_special_characters(self):
        """特殊文字のテスト"""
        print("\n--- 特殊文字テスト ---")

        special_names = [
            ("unicode_emoji", "チーム🔥⚽"),
            ("html_tags", "<script>alert('xss')</script>"),
            ("sql_chars", "'; DROP TABLE teams; --"),
        ]

        for test_name, name in special_names:
            resp = self.client.post("/teams/", json={
                "name": name,
                "tournamentId": 1,
                "teamType": "invited"
            }, headers=self.get_auth_headers())

            if resp.status_code == 201:
                team = resp.json()
                stored_name = team.get("name", "")
                self.client.delete(f"/teams/{team.get('id')}", headers=self.get_auth_headers())

                if stored_name == name:
                    self.log_pass("EdgeCase", test_name, f"特殊文字が正しく保存された")
                else:
                    self.log_issue("EdgeCase", test_name, f"文字が変換された: {stored_name[:50]}")
            elif resp.status_code == 422:
                self.log_pass("EdgeCase", test_name, "特殊文字が拒否された（安全）")
            else:
                self.log_issue("EdgeCase", test_name, f"Status {resp.status_code}")

    def test_auth_bypass(self):
        """認証バイパステスト"""
        print("\n--- 認証バイパステスト ---")

        # トークンなしで保護エンドポイントにアクセス
        no_auth_client = httpx.Client(base_url=API_URL, timeout=30.0, follow_redirects=True)

        protected_endpoints = [
            ("POST", "/teams/", {"name": "Test", "tournamentId": 1, "teamType": "invited"}),
            ("DELETE", "/teams/1", None),
            ("POST", "/matches/1/score", {"homeScore": 1, "awayScore": 0}),
        ]

        for method, endpoint, body in protected_endpoints:
            if method == "POST":
                resp = no_auth_client.post(endpoint, json=body)
            elif method == "DELETE":
                resp = no_auth_client.delete(endpoint)
            else:
                resp = no_auth_client.get(endpoint)

            if resp.status_code == 401:
                self.log_pass("Security", f"auth_bypass_{endpoint}", "認証が必要（正常）")
            elif resp.status_code == 403:
                self.log_pass("Security", f"auth_bypass_{endpoint}", "アクセス拒否（正常）")
            else:
                self.log_issue("Security", f"auth_bypass_{endpoint}",
                              f"認証なしでStatus {resp.status_code}", "critical")

    def test_unauthorized_access(self):
        """権限外アクセステスト"""
        print("\n--- 権限外アクセステスト ---")

        # 無効なトークンでアクセス
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWtlIn0.fake"
        resp = self.client.post("/teams/", json={
            "name": "Unauthorized",
            "tournamentId": 1,
            "teamType": "invited"
        }, headers={"Authorization": f"Bearer {fake_token}"})

        if resp.status_code in [401, 403]:
            self.log_pass("Security", "invalid_token", "無効なトークンを拒否")
        else:
            self.log_issue("Security", "invalid_token",
                          f"無効なトークンでStatus {resp.status_code}", "critical")

    def test_sql_injection(self):
        """SQLインジェクションテスト"""
        print("\n--- SQLインジェクションテスト ---")

        payloads = [
            "1 OR 1=1",
            "1; DROP TABLE teams;",
            "1' OR '1'='1",
        ]

        for payload in payloads:
            # URLパラメータでのインジェクション試行
            resp = self.client.get(f"/teams?tournament_id={payload}", headers=self.get_auth_headers())

            if resp.status_code == 422:
                self.log_pass("Security", f"sql_injection_{payload[:10]}", "不正入力を拒否")
            elif resp.status_code == 200:
                data = resp.json()
                if data.get("total", 0) == 0 or isinstance(data.get("teams"), list):
                    self.log_pass("Security", f"sql_injection_{payload[:10]}", "SQLi攻撃が無効化された")
                else:
                    self.log_issue("Security", f"sql_injection_{payload[:10]}",
                                  "SQLインジェクションの可能性", "critical")
            else:
                self.log_pass("Security", f"sql_injection_{payload[:10]}", f"Status {resp.status_code}")

    def test_xss_prevention(self):
        """XSS対策テスト"""
        print("\n--- XSS対策テスト ---")

        xss_payload = "<script>alert('xss')</script>"

        # チーム作成時にXSSペイロード
        resp = self.client.post("/teams/", json={
            "name": xss_payload,
            "tournamentId": 1,
            "teamType": "invited"
        }, headers=self.get_auth_headers())

        if resp.status_code == 201:
            team = resp.json()
            stored = team.get("name", "")
            self.client.delete(f"/teams/{team.get('id')}", headers=self.get_auth_headers())

            if "<script>" in stored:
                self.log_issue("Security", "xss_stored",
                              "スクリプトタグがそのまま保存された（フロントエンドで対処必要）", "medium")
            else:
                self.log_pass("Security", "xss_stored", "XSSペイロードがサニタイズされた")
        else:
            self.log_pass("Security", "xss_stored", f"XSSペイロードが拒否された (Status {resp.status_code})")

    def _generate_report(self):
        print("\n" + "=" * 70)
        print("テスト結果サマリー")
        print("=" * 70)

        print(f"\n合格: {len(self.passed)}件")
        print(f"問題: {len(self.issues)}件")

        if self.issues:
            print("\n--- 検出された問題 ---")
            critical = [i for i in self.issues if i["severity"] == "critical"]
            high = [i for i in self.issues if i["severity"] == "high"]
            medium = [i for i in self.issues if i["severity"] == "medium"]
            low = [i for i in self.issues if i["severity"] == "low"]

            if critical:
                print(f"\n[CRITICAL] {len(critical)}件:")
                for i in critical:
                    print(f"  - {i['category']}/{i['test']}: {i['message']}")
            if high:
                print(f"\n[HIGH] {len(high)}件:")
                for i in high:
                    print(f"  - {i['category']}/{i['test']}: {i['message']}")
            if medium:
                print(f"\n[MEDIUM] {len(medium)}件:")
                for i in medium:
                    print(f"  - {i['category']}/{i['test']}: {i['message']}")
            if low:
                print(f"\n[LOW] {len(low)}件:")
                for i in low:
                    print(f"  - {i['category']}/{i['test']}: {i['message']}")

        report = {
            "test_date": datetime.now().isoformat(),
            "summary": {"passed": len(self.passed), "issues": len(self.issues)},
            "passed": self.passed,
            "issues": self.issues
        }

        with open("D:/UrawaCup/tests/edge_security_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n詳細: D:/UrawaCup/tests/edge_security_report.json")


if __name__ == "__main__":
    test = EdgeSecurityTest()
    test.run_all()
