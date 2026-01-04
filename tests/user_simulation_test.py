"""
浦和カップ - ユーザー操作シミュレーションテスト
実際のユーザーが行う操作を順番に実行して問題を検出する
"""

import json
import httpx
from datetime import datetime, date

API_URL = "http://localhost:8100/api"

class UserSimulationTest:
    def __init__(self):
        self.client = httpx.Client(base_url=API_URL, timeout=30.0, follow_redirects=True)
        self.token = None
        self.issues = []
        self.successes = []

    def log_issue(self, scenario, message, details=None):
        entry = {
            "scenario": scenario,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.issues.append(entry)
        print(f"[ISSUE] {scenario}: {message}")
        if details:
            print(f"        → {details}")

    def log_success(self, scenario, message):
        self.successes.append({"scenario": scenario, "message": message})
        print(f"[OK] {scenario}: {message}")

    def get_auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def run_all_tests(self):
        print("=" * 70)
        print("浦和カップ ユーザー操作シミュレーションテスト")
        print("=" * 70)

        # シナリオ1: 管理者ログイン
        self.test_admin_login()

        # シナリオ2: ダッシュボード表示（トーナメント一覧）
        self.test_dashboard()

        # シナリオ3: トーナメント詳細表示
        self.test_tournament_detail()

        # シナリオ4: チーム管理
        self.test_team_management()

        # シナリオ5: 試合スケジュール確認
        self.test_match_schedule()

        # シナリオ6: 試合結果入力
        self.test_match_result_entry()

        # シナリオ7: 順位表確認
        self.test_standings()

        # シナリオ8: 得点ランキング確認
        self.test_scorer_ranking()

        # シナリオ9: 会場管理
        self.test_venue_management()

        # シナリオ10: レポート生成
        self.test_report_generation()

        # シナリオ11: パブリックビュー
        self.test_public_views()

        # 結果サマリー
        self._generate_report()

    def test_admin_login(self):
        """シナリオ1: 管理者としてログイン"""
        print("\n--- シナリオ1: 管理者ログイン ---")

        try:
            resp = self.client.post("/auth/login", json={
                "username": "admin",
                "password": "admin1234"
            })

            if resp.status_code == 200:
                data = resp.json()
                if "accessToken" in data:
                    self.token = data["accessToken"]
                    self.log_success("ログイン", "管理者ログイン成功")
                elif "access_token" in data:
                    self.token = data["access_token"]
                    self.log_issue("ログイン", "snake_case 'access_token' を使用",
                                   "フロントエンドでエラーになる可能性")
                else:
                    self.log_issue("ログイン", "トークンが見つからない", data)
            else:
                self.log_issue("ログイン", f"ログイン失敗 (Status: {resp.status_code})",
                              resp.text[:200])
        except Exception as e:
            self.log_issue("ログイン", "接続エラー", str(e))

    def test_dashboard(self):
        """シナリオ2: ダッシュボード（トーナメント一覧）表示"""
        print("\n--- シナリオ2: ダッシュボード表示 ---")

        try:
            resp = self.client.get("/tournaments", headers=self.get_auth_headers())

            if resp.status_code == 200:
                data = resp.json()
                tournaments = data.get("tournaments", [])
                total = data.get("total", len(tournaments))

                if total > 0:
                    self.log_success("ダッシュボード", f"トーナメント {total}件 表示")

                    # フィールド名チェック
                    if tournaments:
                        t = tournaments[0]
                        snake_fields = [k for k in t.keys() if "_" in k and not k.startswith("_")]
                        if snake_fields:
                            self.log_issue("ダッシュボード",
                                          f"snake_caseフィールド検出: {snake_fields[:3]}")
                else:
                    self.log_success("ダッシュボード", "トーナメント 0件（データ未登録）")
            else:
                self.log_issue("ダッシュボード", f"取得失敗 (Status: {resp.status_code})")
        except Exception as e:
            self.log_issue("ダッシュボード", "エラー", str(e))

    def test_tournament_detail(self):
        """シナリオ3: トーナメント詳細表示"""
        print("\n--- シナリオ3: トーナメント詳細 ---")

        try:
            resp = self.client.get("/tournaments/1", headers=self.get_auth_headers())

            if resp.status_code == 200:
                data = resp.json()

                # 日付フィールドのチェック（Issue #018の原因）
                if "startDate" in data:
                    try:
                        # 日付パースをシミュレート
                        start_date = data["startDate"]
                        if start_date:
                            # JavaScriptのnew Date()と同様のパース
                            parsed = datetime.fromisoformat(start_date.replace("Z", "+00:00") if "Z" in start_date else start_date)
                            self.log_success("トーナメント詳細",
                                           f"startDate={start_date} パース成功")
                        else:
                            self.log_issue("トーナメント詳細", "startDateがnull/空")
                    except Exception as e:
                        self.log_issue("トーナメント詳細",
                                      f"startDateのパース失敗: {start_date}", str(e))
                elif "start_date" in data:
                    self.log_issue("トーナメント詳細",
                                  "start_date (snake_case) が使われている",
                                  "フロントエンドでInvalid time valueエラーの原因")
                else:
                    self.log_issue("トーナメント詳細", "startDateフィールドが存在しない")

                # 他の必須フィールドチェック
                required = ["id", "name"]
                missing = [f for f in required if f not in data]
                if missing:
                    self.log_issue("トーナメント詳細", f"必須フィールド不足: {missing}")

            elif resp.status_code == 404:
                self.log_success("トーナメント詳細", "ID=1 が存在しない（正常）")
            else:
                self.log_issue("トーナメント詳細", f"取得失敗 (Status: {resp.status_code})")
        except Exception as e:
            self.log_issue("トーナメント詳細", "エラー", str(e))

    def test_team_management(self):
        """シナリオ4: チーム管理"""
        print("\n--- シナリオ4: チーム管理 ---")

        try:
            # チーム一覧取得
            resp = self.client.get("/teams",
                                   params={"tournament_id": 1},
                                   headers=self.get_auth_headers())

            if resp.status_code == 200:
                data = resp.json()
                teams = data.get("teams", [])
                self.log_success("チーム一覧", f"{len(teams)}チーム表示")

                # チームデータのフィールドチェック
                if teams:
                    team = teams[0]
                    # groupIdがあるか確認
                    if "group_id" in team and "groupId" not in team:
                        self.log_issue("チーム一覧", "group_id (snake_case) が使われている")
            else:
                self.log_issue("チーム一覧", f"取得失敗 (Status: {resp.status_code})")

            # チーム作成テスト（POSTできるか確認）
            test_team = {
                "name": f"テストチーム_{datetime.now().strftime('%H%M%S')}",
                "tournamentId": 1,
                "teamType": "invited"
            }
            resp = self.client.post("/teams",
                                    json=test_team,
                                    headers=self.get_auth_headers())

            if resp.status_code in [200, 201]:
                self.log_success("チーム作成", "新規チーム作成成功")
                # 作成したチームのIDを取得して削除
                created_team = resp.json()
                team_id = created_team.get("id")
                if team_id:
                    del_resp = self.client.delete(f"/teams/{team_id}",
                                                  headers=self.get_auth_headers())
                    if del_resp.status_code in [200, 204]:
                        self.log_success("チーム削除", "テストチーム削除成功")
            elif resp.status_code == 422:
                # バリデーションエラー - フィールド名の問題かも
                self.log_issue("チーム作成", "バリデーションエラー", resp.json())
            elif resp.status_code == 401:
                self.log_issue("チーム作成", "認証エラー（トークンが無効）")
            else:
                self.log_issue("チーム作成", f"失敗 (Status: {resp.status_code})", resp.text[:200])

        except Exception as e:
            self.log_issue("チーム管理", "エラー", str(e))

    def test_match_schedule(self):
        """シナリオ5: 試合スケジュール確認"""
        print("\n--- シナリオ5: 試合スケジュール ---")

        try:
            resp = self.client.get("/matches",
                                   params={"tournament_id": 1, "limit": 20},
                                   headers=self.get_auth_headers())

            if resp.status_code == 200:
                data = resp.json()
                matches = data.get("matches", [])
                total = data.get("total", len(matches))

                self.log_success("試合スケジュール", f"{total}試合表示")

                if matches:
                    match = matches[0]
                    # 日付/時刻フィールドのチェック
                    date_fields = {
                        "matchDate": match.get("matchDate"),
                        "match_date": match.get("match_date"),
                        "matchTime": match.get("matchTime"),
                        "match_time": match.get("match_time"),
                    }

                    snake_fields = [k for k, v in date_fields.items() if v and "_" in k]
                    if snake_fields:
                        self.log_issue("試合スケジュール",
                                      f"snake_caseフィールド: {snake_fields}")

                    # チーム名の表示確認
                    home_team = match.get("homeTeam") or match.get("home_team")
                    away_team = match.get("awayTeam") or match.get("away_team")

                    if home_team and away_team:
                        self.log_success("試合スケジュール",
                                        f"チーム名表示OK: {home_team.get('name', 'N/A')} vs {away_team.get('name', 'N/A')}")
            else:
                self.log_issue("試合スケジュール", f"取得失敗 (Status: {resp.status_code})")
        except Exception as e:
            self.log_issue("試合スケジュール", "エラー", str(e))

    def test_match_result_entry(self):
        """シナリオ6: 試合結果入力"""
        print("\n--- シナリオ6: 試合結果入力 ---")

        try:
            # まず試合を取得
            resp = self.client.get("/matches",
                                   params={"tournament_id": 1, "limit": 1},
                                   headers=self.get_auth_headers())

            if resp.status_code == 200:
                data = resp.json()
                matches = data.get("matches", [])

                if matches:
                    match = matches[0]
                    match_id = match.get("id")

                    # スコア入力をシミュレート
                    score_data = {
                        "homeScoreHalf1": 1,
                        "homeScoreHalf2": 1,
                        "awayScoreHalf1": 0,
                        "awayScoreHalf2": 1,
                        "status": "finished"
                    }

                    resp = self.client.put(f"/matches/{match_id}/score",
                                          json=score_data,
                                          headers=self.get_auth_headers())

                    if resp.status_code == 200:
                        self.log_success("試合結果入力", f"Match #{match_id} スコア更新成功")
                    elif resp.status_code == 422:
                        # フィールド名の問題かもしれない
                        error = resp.json()
                        self.log_issue("試合結果入力", "バリデーションエラー", error)

                        # snake_caseで再試行
                        score_data_snake = {
                            "home_score": 2,
                            "away_score": 1,
                            "home_score_half": 1,
                            "away_score_half": 0,
                            "status": "finished"
                        }
                        resp2 = self.client.put(f"/matches/{match_id}/score",
                                               json=score_data_snake,
                                               headers=self.get_auth_headers())
                        if resp2.status_code == 200:
                            self.log_issue("試合結果入力",
                                          "snake_caseフィールドが必要",
                                          "フロントエンドとの不整合の可能性")
                    else:
                        self.log_issue("試合結果入力", f"失敗 (Status: {resp.status_code})")
                else:
                    self.log_success("試合結果入力", "試合データなし（スキップ）")
            else:
                self.log_issue("試合結果入力", "試合取得失敗")
        except Exception as e:
            self.log_issue("試合結果入力", "エラー", str(e))

    def test_standings(self):
        """シナリオ7: 順位表確認"""
        print("\n--- シナリオ7: 順位表 ---")

        try:
            resp = self.client.get("/standings/1", headers=self.get_auth_headers())

            if resp.status_code == 200:
                data = resp.json()

                if isinstance(data, list):
                    self.log_success("順位表", f"{len(data)}グループの順位表表示")

                    if data:
                        # フィールドチェック
                        standing = data[0] if isinstance(data[0], dict) else data[0][0] if data[0] else None
                        if standing:
                            snake_fields = [k for k in standing.keys() if "_" in k and not k.startswith("_")]
                            if snake_fields:
                                self.log_issue("順位表", f"snake_caseフィールド: {snake_fields[:5]}")
                elif isinstance(data, dict):
                    self.log_success("順位表", "順位表データ取得成功")
            elif resp.status_code == 404:
                self.log_success("順位表", "順位データなし（正常）")
            else:
                self.log_issue("順位表", f"取得失敗 (Status: {resp.status_code})")
        except Exception as e:
            self.log_issue("順位表", "エラー", str(e))

    def test_scorer_ranking(self):
        """シナリオ8: 得点ランキング確認"""
        print("\n--- シナリオ8: 得点ランキング ---")

        try:
            resp = self.client.get("/standings/1/top-scorers",
                                   headers=self.get_auth_headers())

            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    self.log_success("得点ランキング", f"{len(data)}名の得点者表示")
                else:
                    self.log_success("得点ランキング", "データ取得成功")
            elif resp.status_code == 404:
                self.log_success("得点ランキング", "得点データなし（正常）")
            else:
                self.log_issue("得点ランキング", f"取得失敗 (Status: {resp.status_code})")
        except Exception as e:
            self.log_issue("得点ランキング", "エラー", str(e))

    def test_venue_management(self):
        """シナリオ9: 会場管理"""
        print("\n--- シナリオ9: 会場管理 ---")

        try:
            resp = self.client.get("/venues",
                                   params={"tournament_id": 1},
                                   headers=self.get_auth_headers())

            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    self.log_success("会場一覧", f"{len(data)}会場表示")
                elif isinstance(data, dict) and "venues" in data:
                    self.log_success("会場一覧", f"{len(data['venues'])}会場表示")
                else:
                    self.log_success("会場一覧", "データ取得成功")
            else:
                self.log_issue("会場一覧", f"取得失敗 (Status: {resp.status_code})")
        except Exception as e:
            self.log_issue("会場管理", "エラー", str(e))

    def test_report_generation(self):
        """シナリオ10: レポート生成"""
        print("\n--- シナリオ10: レポート生成 ---")

        try:
            # PDF生成
            resp = self.client.get("/reports/tournament/1/pdf",
                                   headers=self.get_auth_headers())

            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "")
                if "pdf" in content_type or len(resp.content) > 1000:
                    self.log_success("PDFレポート", "PDF生成成功")
                else:
                    self.log_issue("PDFレポート", "PDFコンテンツが不正")
            elif resp.status_code == 404:
                self.log_success("PDFレポート", "トーナメントデータなし（スキップ）")
            else:
                self.log_issue("PDFレポート", f"生成失敗 (Status: {resp.status_code})")

            # Excel生成
            resp = self.client.get("/reports/tournament/1/excel",
                                   headers=self.get_auth_headers())

            if resp.status_code == 200:
                self.log_success("Excelレポート", "Excel生成成功")
            elif resp.status_code == 404:
                self.log_success("Excelレポート", "トーナメントデータなし（スキップ）")
            else:
                self.log_issue("Excelレポート", f"生成失敗 (Status: {resp.status_code})")

        except Exception as e:
            self.log_issue("レポート生成", "エラー", str(e))

    def test_public_views(self):
        """シナリオ11: パブリックビュー（認証なし）"""
        print("\n--- シナリオ11: パブリックビュー ---")

        # 認証なしでアクセス
        public_client = httpx.Client(base_url=API_URL, timeout=30.0, follow_redirects=True)

        try:
            # パブリック順位表
            resp = public_client.get("/public/standings/1")

            if resp.status_code == 200:
                self.log_success("パブリック順位表", "認証なしでアクセス可能")
            elif resp.status_code == 404:
                self.log_success("パブリック順位表", "エンドポイント未実装or データなし")
            elif resp.status_code == 401:
                self.log_issue("パブリック順位表", "認証が必要（パブリックビューになっていない）")
            else:
                self.log_issue("パブリック順位表", f"Status: {resp.status_code}")

            # パブリック試合一覧
            resp = public_client.get("/public/matches/1")

            if resp.status_code == 200:
                self.log_success("パブリック試合一覧", "認証なしでアクセス可能")
            elif resp.status_code == 404:
                self.log_success("パブリック試合一覧", "エンドポイント未実装or データなし")
            elif resp.status_code == 401:
                self.log_issue("パブリック試合一覧", "認証が必要（パブリックビューになっていない）")
            else:
                self.log_issue("パブリック試合一覧", f"Status: {resp.status_code}")

        except Exception as e:
            self.log_issue("パブリックビュー", "エラー", str(e))
        finally:
            public_client.close()

    def _generate_report(self):
        """テスト結果レポート"""
        print("\n" + "=" * 70)
        print("テスト結果サマリー")
        print("=" * 70)

        print(f"\n成功: {len(self.successes)}件")
        print(f"問題: {len(self.issues)}件")

        if self.issues:
            print("\n" + "-" * 40)
            print("検出された問題:")
            print("-" * 40)
            for issue in self.issues:
                print(f"\n[{issue['scenario']}]")
                print(f"  {issue['message']}")
                if issue.get('details'):
                    print(f"  詳細: {issue['details']}")

        # JSON保存
        report = {
            "test_date": datetime.now().isoformat(),
            "summary": {
                "successes": len(self.successes),
                "issues": len(self.issues)
            },
            "successes": self.successes,
            "issues": self.issues
        }

        with open("D:/UrawaCup/tests/user_simulation_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n詳細レポート: D:/UrawaCup/tests/user_simulation_report.json")

        return report


if __name__ == "__main__":
    test = UserSimulationTest()
    test.run_all_tests()
