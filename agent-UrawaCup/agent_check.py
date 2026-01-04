#!/usr/bin/env python3
"""
agent-Check: UrawaCup操作テストエージェント
Claude Agent SDKを使用してユーザー操作をテストし、動作確認を行う
不明点や問題はISSUES.mdに記録する
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage
except ImportError:
    print("Error: claude-agent-sdk is not installed.")
    print("Install with: pip install claude-agent-sdk")
    sys.exit(1)

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# プロジェクトルート
PROJECT_ROOT = Path("D:/UrawaCup")
ISSUES_FILE = PROJECT_ROOT / "ISSUES.md"

# テストシナリオ定義（プロジェクト要件に特化）
# FinalDay_Logic_Final.md と Report_PDF_Specification.md に基づく
TEST_SCENARIOS = [
    # ========== 基本インフラ ==========
    {
        "id": "T001",
        "name": "バックエンドAPI接続確認",
        "prompt": """
バックエンドAPIが正常に動作しているか確認：
curl http://localhost:8000/api/docs にアクセスしてレスポンスを確認
結果を報告（成功/失敗）
""",
        "tools": ["Bash"],
        "category": "infrastructure"
    },
    {
        "id": "T002",
        "name": "フロントエンドビルド確認",
        "prompt": """
フロントエンドのビルドエラーがないか確認：
cd D:/UrawaCup/src/frontend && npm run build 2>&1 | head -30
結果を報告（成功/失敗とエラー内容）
""",
        "tools": ["Bash"],
        "category": "infrastructure"
    },
    # ========== 最終日ロジック（FinalDay_Logic_Final.md） ==========
    {
        "id": "T003",
        "name": "最終日API確認",
        "prompt": """
最終日関連のAPIエンドポイントを確認：
1. curl http://localhost:8000/api/docs でOpenAPI仕様を取得
2. final-day または finals 関連のエンドポイントを探す
3. generate-finals, training, bracket 等のエンドポイント存在確認
結果を報告
""",
        "tools": ["Bash"],
        "category": "final-day"
    },
    {
        "id": "T004",
        "name": "会場Boolean更新確認",
        "prompt": """
会場のforFinalDay, isFinalsVenueフラグが正しく更新されるか確認：
1. curl http://localhost:8000/api/venues/?tournament_id=1 で会場一覧取得
2. 1件の会場を for_final_day=false, is_finals_venue=false に更新
3. 再取得して値が保存されているか確認
問題があれば詳細を報告
""",
        "tools": ["Bash"],
        "category": "final-day"
    },
    {
        "id": "T005",
        "name": "順位リーグ生成確認",
        "prompt": """
D:/UrawaCup/src/backend/routes/matches.py を読んで以下を確認：
1. generate_training_matches エンドポイントが存在するか
2. 12チームを4グループに分配するロジックがあるか
3. 各グループで3試合（総当たり）が生成されるか
問題があれば報告
""",
        "tools": ["Read", "Grep"],
        "category": "final-day"
    },
    {
        "id": "T006",
        "name": "チーム振り分けロジック確認",
        "prompt": """
最終日のチーム振り分けロジックを確認：
1. D:/UrawaCup/src/backend/ で distributeTeams または team.*distribution を検索
2. 予選グループ1-4位を順位リーグに振り分けるロジックがあるか
3. A1位→第1リーグ, A2位→第2リーグ のようなマッピングがあるか
問題があれば報告
""",
        "tools": ["Grep", "Read"],
        "category": "final-day"
    },
    {
        "id": "T007",
        "name": "再戦チェック機能確認",
        "prompt": """
再戦（予選で対戦済み）チェック機能を確認：
1. D:/UrawaCup/src/backend/ で check.*played または rematch を検索
2. FinalDaySchedule.tsx で再戦警告表示があるか確認
3. MatchRow.tsx の isRematch プロップが使われているか確認
問題があれば報告
""",
        "tools": ["Grep", "Read"],
        "category": "final-day"
    },
    {
        "id": "T008",
        "name": "会場担当設定確認",
        "prompt": """
最終日の会場担当（managerTeamId）機能を確認：
1. D:/UrawaCup/src/frontend/src/features/venues/types.ts で managerTeamId が定義されているか
2. VenueCard.tsx で会場担当の編集UIがあるか
3. バックエンドで manager_team_id の更新が可能か
問題があれば報告
""",
        "tools": ["Read", "Grep"],
        "category": "final-day"
    },
    {
        "id": "T009",
        "name": "決勝トーナメント反映確認",
        "prompt": """
準決勝結果の3決・決勝への反映機能を確認：
1. D:/UrawaCup/src/backend/ で update.*bracket または finals.*bracket を検索
2. FinalDaySchedule.tsx に handleUpdateBracket 関数があるか
3. 準決勝勝者→決勝、敗者→3決 のロジックがあるか
問題があれば報告
""",
        "tools": ["Grep", "Read"],
        "category": "final-day"
    },
    {
        "id": "T010",
        "name": "ドラッグ&ドロップ連打防止",
        "prompt": """
チーム入れ替え時の連打防止が実装されているか確認：
1. FinalDaySchedule.tsx で swappingRef が使われているか
2. MatchSchedule.tsx で同様の実装があるか
3. 重複API呼び出しを防止するロジックを確認
問題があれば報告
""",
        "tools": ["Grep", "Read"],
        "category": "final-day"
    },
    # ========== PDF報告書（Report_PDF_Specification.md） ==========
    {
        "id": "T011",
        "name": "PDF生成API確認",
        "prompt": """
PDF報告書生成APIを確認：
1. curl http://localhost:8000/api/docs でreports関連エンドポイントを探す
2. /api/reports/ または /api/reports/generate のエンドポイントがあるか
3. PDF生成パラメータを確認
問題があれば報告
""",
        "tools": ["Bash"],
        "category": "report"
    },
    {
        "id": "T012",
        "name": "送信元設定API確認",
        "prompt": """
報告書の送信元設定APIを確認：
1. D:/UrawaCup/src/backend/routes/reports.py を読む
2. sender-settings エンドポイントがあるか
3. GET/PATCH で senderOrganization, senderName, senderContact が操作できるか
問題があれば報告
""",
        "tools": ["Read", "Bash"],
        "category": "report"
    },
    {
        "id": "T013",
        "name": "PDF余白・フォント設定確認",
        "prompt": """
PDF出力の仕様を確認（Report_PDF_Specification.md準拠）：
1. D:/UrawaCup/src/backend/routes/reports.py または reports_excel.py を読む
2. マージン設定（仕様: 15mm）を確認
3. フォントサイズ（仕様: ヘッダー11pt, タイトル16pt, 本文11pt）を確認
問題があれば報告
""",
        "tools": ["Read"],
        "category": "report"
    },
    {
        "id": "T014",
        "name": "報告書フロントエンドUI確認",
        "prompt": """
報告書画面のUIを確認：
1. D:/UrawaCup/src/frontend/src/pages/Reports.tsx を読む
2. 送信元設定の編集UIがあるか
3. PDF生成ボタンと日付選択UIがあるか
問題があれば報告
""",
        "tools": ["Read"],
        "category": "report"
    },
    # ========== データ整合性 ==========
    {
        "id": "T015",
        "name": "試合ステージ分類確認",
        "prompt": """
最終日の試合ステージが正しく分類されているか確認：
1. curl http://localhost:8000/api/matches/?tournament_id=1 で試合取得
2. matchType別の試合数をカウント（semifinal: 2, third_place: 1, final: 1, training: 複数）
3. 決勝トーナメントが正しい会場（駒場スタジアム等）で開催されているか
問題があれば報告
""",
        "tools": ["Bash"],
        "category": "data"
    },
    {
        "id": "T016",
        "name": "チーム入れ替えAPI確認",
        "prompt": """
チーム入れ替えAPIを確認：
1. /api/matches/swap-teams エンドポイントの存在確認
2. パラメータ（match1Id, side1, match2Id, side2）を確認
3. 正常にチームが入れ替わるか
問題があれば報告
""",
        "tools": ["Bash"],
        "category": "data"
    },
]


class TestResult:
    """テスト結果を格納するクラス"""
    def __init__(self, test_id: str, name: str, category: str):
        self.test_id = test_id
        self.name = name
        self.category = category
        self.status: Optional[str] = None  # "PASS", "FAIL", "ERROR"
        self.message: str = ""
        self.issues: list[str] = []  # 発見された問題
        self.duration: float = 0.0


class IssueTracker:
    """イシュー追跡クラス"""
    def __init__(self, issues_file: Path):
        self.issues_file = issues_file
        self.issues: list[dict] = []

    def add_issue(self, test_id: str, test_name: str, category: str,
                  issue_type: str, description: str, details: str = ""):
        """イシューを追加"""
        self.issues.append({
            "timestamp": datetime.now().isoformat(),
            "test_id": test_id,
            "test_name": test_name,
            "category": category,
            "type": issue_type,  # "BUG", "QUESTION", "IMPROVEMENT"
            "description": description,
            "details": details
        })

    def save(self):
        """イシューをファイルに保存"""
        if not self.issues:
            return

        # 既存の内容を読み込み
        existing_content = ""
        if self.issues_file.exists():
            existing_content = self.issues_file.read_text(encoding="utf-8")

        # 新しいイシューを追加
        new_section = f"\n\n## テスト実行: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        for issue in self.issues:
            icon = {
                "BUG": "🐛",
                "QUESTION": "❓",
                "IMPROVEMENT": "💡",
                "ERROR": "❌"
            }.get(issue["type"], "📝")

            new_section += f"""### {icon} [{issue['test_id']}] {issue['description']}

- **カテゴリ**: {issue['category']}
- **テスト**: {issue['test_name']}
- **タイプ**: {issue['type']}
- **検出日時**: {issue['timestamp']}

{issue['details']}

---

"""

        # ファイルに書き込み
        if not existing_content:
            header = """# UrawaCup - Issues & Questions

このファイルはagent-Checkによって自動生成されます。
テスト実行中に発見された問題や不明点を記録します。

"""
            existing_content = header

        with open(self.issues_file, "w", encoding="utf-8") as f:
            f.write(existing_content + new_section)

        console.print(f"[yellow]イシューを記録しました: {self.issues_file}[/yellow]")


# グローバルイシュートラッカー
issue_tracker = IssueTracker(ISSUES_FILE)


async def run_single_test(scenario: dict, results: list[TestResult]) -> TestResult:
    """単一のテストシナリオを実行"""
    result = TestResult(
        test_id=scenario["id"],
        name=scenario["name"],
        category=scenario["category"]
    )

    start_time = datetime.now()
    full_response = []

    try:
        async for message in query(
            prompt=scenario["prompt"] + "\n\n不明点や問題があれば、必ず報告してください。",
            options=ClaudeAgentOptions(
                allowed_tools=scenario["tools"],
                max_turns=15,
            )
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if hasattr(block, "text"):
                        full_response.append(block.text)
            elif isinstance(message, ResultMessage):
                if message.subtype == "success":
                    result.status = "PASS"
                else:
                    result.status = "FAIL"

        result.message = "\n".join(full_response)

        # レスポンスから成功/失敗を判定
        response_text = result.message.lower()

        # エラーキーワードの検出
        error_keywords = ["error", "failed", "失敗", "エラー", "問題", "不明", "見つかりません"]
        has_error = any(keyword in response_text for keyword in error_keywords)

        if has_error:
            result.status = "FAIL"
            # イシューを記録
            issue_tracker.add_issue(
                test_id=result.test_id,
                test_name=result.name,
                category=result.category,
                issue_type="BUG" if "error" in response_text or "エラー" in response_text else "QUESTION",
                description=f"{result.name}で問題を検出",
                details=result.message[-1000:] if len(result.message) > 1000 else result.message
            )
        elif result.status is None:
            result.status = "PASS"

        # 不明点キーワードの検出
        question_keywords = ["不明", "わからない", "確認が必要", "要調査"]
        if any(keyword in response_text for keyword in question_keywords):
            issue_tracker.add_issue(
                test_id=result.test_id,
                test_name=result.name,
                category=result.category,
                issue_type="QUESTION",
                description=f"{result.name}で不明点を検出",
                details=result.message[-1000:] if len(result.message) > 1000 else result.message
            )

    except Exception as e:
        result.status = "ERROR"
        result.message = str(e)
        issue_tracker.add_issue(
            test_id=result.test_id,
            test_name=result.name,
            category=result.category,
            issue_type="ERROR",
            description=f"{result.name}で実行エラー",
            details=str(e)
        )

    result.duration = (datetime.now() - start_time).total_seconds()
    results.append(result)
    return result


async def run_all_tests(categories: Optional[list[str]] = None) -> list[TestResult]:
    """全テストを実行"""
    results: list[TestResult] = []

    # カテゴリフィルタ
    scenarios = TEST_SCENARIOS
    if categories:
        scenarios = [s for s in scenarios if s["category"] in categories]

    console.print(Panel.fit(
        f"[bold blue]UrawaCup操作テスト開始[/bold blue]\n"
        f"テスト数: {len(scenarios)}\n"
        f"イシュー記録先: {ISSUES_FILE}",
        title="agent-Check"
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for scenario in scenarios:
            task = progress.add_task(
                f"[cyan]{scenario['id']}[/cyan] {scenario['name']}...",
                total=1
            )

            result = await run_single_test(scenario, results)

            status_icon = {
                "PASS": "[green]✓[/green]",
                "FAIL": "[red]✗[/red]",
                "ERROR": "[yellow]![/yellow]"
            }.get(result.status, "?")

            progress.update(task, description=f"{status_icon} {scenario['name']}")
            progress.advance(task)

    # イシューを保存
    issue_tracker.save()

    return results


def print_results(results: list[TestResult]):
    """テスト結果を表示"""
    table = Table(title="テスト結果サマリー")
    table.add_column("ID", style="cyan")
    table.add_column("テスト名", style="white")
    table.add_column("カテゴリ", style="blue")
    table.add_column("結果", style="bold")
    table.add_column("時間(s)", style="dim")

    pass_count = 0
    fail_count = 0
    error_count = 0

    for result in results:
        status_style = {
            "PASS": "[green]PASS[/green]",
            "FAIL": "[red]FAIL[/red]",
            "ERROR": "[yellow]ERROR[/yellow]"
        }.get(result.status, result.status)

        if result.status == "PASS":
            pass_count += 1
        elif result.status == "FAIL":
            fail_count += 1
        else:
            error_count += 1

        table.add_row(
            result.test_id,
            result.name,
            result.category,
            status_style,
            f"{result.duration:.1f}"
        )

    console.print(table)

    # サマリー
    total = len(results)
    console.print(Panel(
        f"[green]PASS: {pass_count}[/green] | "
        f"[red]FAIL: {fail_count}[/red] | "
        f"[yellow]ERROR: {error_count}[/yellow] | "
        f"Total: {total}\n"
        f"Issues recorded: {len(issue_tracker.issues)}",
        title="結果サマリー"
    ))

    # 失敗したテストの詳細
    failed = [r for r in results if r.status != "PASS"]
    if failed:
        console.print("\n[bold red]失敗したテストの詳細:[/bold red]")
        for result in failed:
            console.print(f"\n[cyan]{result.test_id}[/cyan] {result.name}")
            msg = result.message[:500] + "..." if len(result.message) > 500 else result.message
            console.print(f"[dim]{msg}[/dim]")


def main():
    """メインエントリポイント"""
    import argparse

    parser = argparse.ArgumentParser(
        description="UrawaCup操作テストエージェント（不明点はISSUES.mdに記録）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
カテゴリ（プロジェクト要件に特化）:
  infrastructure  - インフラ接続・ビルド確認
  final-day       - 最終日ロジック（FinalDay_Logic_Final.md）
  report          - PDF報告書（Report_PDF_Specification.md）
  data            - データ整合性

使用例:
  python agent_check.py                    # 全テスト実行（16件）
  python agent_check.py -c final-day       # 最終日関連のみ
  python agent_check.py -c report          # 報告書関連のみ
  python agent_check.py --list             # テスト一覧表示

不明点や問題は D:/UrawaCup/ISSUES.md に自動記録されます。
"""
    )
    parser.add_argument(
        "-c", "--category",
        nargs="+",
        help="テストするカテゴリを指定"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="テスト一覧を表示"
    )
    parser.add_argument(
        "--issues",
        action="store_true",
        help="現在のイシューを表示"
    )

    args = parser.parse_args()

    if args.list:
        table = Table(title="テストシナリオ一覧")
        table.add_column("ID", style="cyan")
        table.add_column("名前", style="white")
        table.add_column("カテゴリ", style="blue")
        table.add_column("ツール", style="dim")

        for scenario in TEST_SCENARIOS:
            table.add_row(
                scenario["id"],
                scenario["name"],
                scenario["category"],
                ", ".join(scenario["tools"])
            )

        console.print(table)
        return

    if args.issues:
        if ISSUES_FILE.exists():
            console.print(Panel(ISSUES_FILE.read_text(encoding="utf-8"), title="ISSUES.md"))
        else:
            console.print("[yellow]イシューファイルはまだありません[/yellow]")
        return

    # テスト実行
    try:
        results = asyncio.run(run_all_tests(args.category))
        print_results(results)

        # 失敗があれば終了コード1
        if any(r.status != "PASS" for r in results):
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]テスト中断[/yellow]")
        issue_tracker.save()  # 中断時もイシューを保存
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
