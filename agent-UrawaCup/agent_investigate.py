#!/usr/bin/env python3
"""
agent-Investigate: UrawaCupイシュー調査エージェント
Claude Agent SDKを使用してISSUES.mdの問題を調査し、ドキュメントにまとめる
"""

import asyncio
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

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
from rich.markdown import Markdown

console = Console()

# パス設定
PROJECT_ROOT = Path("D:/UrawaCup")
ISSUES_FILE = PROJECT_ROOT / "ISSUES.md"
DOCS_DIR = PROJECT_ROOT / "docs" / "investigations"


class Issue:
    """イシュー情報を格納するクラス"""
    def __init__(self, issue_id: str, title: str, category: str,
                 issue_type: str, test_name: str, details: str):
        self.issue_id = issue_id
        self.title = title
        self.category = category
        self.issue_type = issue_type
        self.test_name = test_name
        self.details = details
        self.investigation: Optional[str] = None
        self.solution: Optional[str] = None
        self.status: str = "pending"  # pending, investigating, resolved, unknown


def parse_issues_file(issues_file: Path) -> list[Issue]:
    """ISSUES.mdをパースしてイシューリストを取得"""
    if not issues_file.exists():
        return []

    content = issues_file.read_text(encoding="utf-8")
    issues = []

    # イシューセクションを抽出
    # パターン: ### 🐛 [T004] タイトル
    pattern = r'### ([🐛❓💡❌📝]) \[([^\]]+)\] (.+?)\n\n- \*\*カテゴリ\*\*: (.+?)\n- \*\*テスト\*\*: (.+?)\n- \*\*タイプ\*\*: (.+?)\n- \*\*検出日時\*\*: (.+?)\n\n(.*?)(?=\n---|\Z)'

    matches = re.findall(pattern, content, re.DOTALL)

    for match in matches:
        icon, issue_id, title, category, test_name, issue_type, timestamp, details = match
        issues.append(Issue(
            issue_id=issue_id,
            title=title.strip(),
            category=category.strip(),
            issue_type=issue_type.strip(),
            test_name=test_name.strip(),
            details=details.strip()
        ))

    return issues


async def investigate_issue(issue: Issue) -> Issue:
    """単一のイシューを調査"""
    prompt = f"""
以下のイシューを調査してください。

## イシュー情報
- **ID**: {issue.issue_id}
- **タイトル**: {issue.title}
- **カテゴリ**: {issue.category}
- **タイプ**: {issue.issue_type}
- **テスト名**: {issue.test_name}

## 詳細
{issue.details}

## 調査してほしいこと
1. このイシューの根本原因を特定してください
2. 関連するコードを確認してください（D:/UrawaCup/src/以下）
3. 解決策を提案してください
4. 必要であれば、修正コードの例を示してください

## 出力形式
以下の形式で回答してください：

### 調査結果
（根本原因の説明）

### 関連コード
（調査したファイルと問題箇所）

### 解決策
（具体的な解決方法）

### 修正コード例
（必要な場合のみ）

### ステータス
（resolved / needs_more_investigation / unknown のいずれか）
"""

    full_response = []

    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                allowed_tools=["Read", "Grep", "Glob", "Bash"],
                max_turns=20,
            )
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if hasattr(block, "text"):
                        full_response.append(block.text)

        issue.investigation = "\n".join(full_response)

        # ステータスを抽出
        investigation_lower = issue.investigation.lower()
        if "resolved" in investigation_lower:
            issue.status = "resolved"
        elif "needs_more_investigation" in investigation_lower or "不明" in investigation_lower:
            issue.status = "needs_more_investigation"
        elif "unknown" in investigation_lower:
            issue.status = "unknown"
        else:
            issue.status = "investigated"

    except Exception as e:
        issue.investigation = f"調査中にエラーが発生: {str(e)}"
        issue.status = "error"

    return issue


def save_investigation_report(issue: Issue, docs_dir: Path) -> Path:
    """調査結果をドキュメントとして保存"""
    docs_dir.mkdir(parents=True, exist_ok=True)

    # ファイル名を生成（安全な文字のみ）
    safe_title = re.sub(r'[^\w\s-]', '', issue.title)[:50]
    filename = f"{issue.issue_id}_{safe_title.replace(' ', '_')}.md"
    filepath = docs_dir / filename

    content = f"""# 調査レポート: {issue.title}

## 基本情報

| 項目 | 値 |
|------|-----|
| イシューID | {issue.issue_id} |
| カテゴリ | {issue.category} |
| タイプ | {issue.issue_type} |
| テスト名 | {issue.test_name} |
| ステータス | {issue.status} |
| 調査日時 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |

## 元のイシュー詳細

{issue.details}

## 調査結果

{issue.investigation}

---
*このレポートは agent-Investigate によって自動生成されました*
"""

    filepath.write_text(content, encoding="utf-8")
    return filepath


def save_summary_report(issues: list[Issue], docs_dir: Path) -> Path:
    """サマリーレポートを保存"""
    filepath = docs_dir / "_SUMMARY.md"

    resolved = [i for i in issues if i.status == "resolved"]
    investigating = [i for i in issues if i.status in ["investigated", "needs_more_investigation"]]
    unknown = [i for i in issues if i.status in ["unknown", "error"]]

    content = f"""# イシュー調査サマリー

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 統計

| ステータス | 件数 |
|-----------|------|
| 解決済み | {len(resolved)} |
| 調査済み（要対応） | {len(investigating)} |
| 不明/エラー | {len(unknown)} |
| **合計** | **{len(issues)}** |

## 解決済みイシュー

"""

    for issue in resolved:
        content += f"- [{issue.issue_id}] {issue.title}\n"

    content += "\n## 要対応イシュー\n\n"

    for issue in investigating:
        content += f"- [{issue.issue_id}] {issue.title} - {issue.category}\n"

    content += "\n## 調査レポート一覧\n\n"

    for issue in issues:
        safe_title = re.sub(r'[^\w\s-]', '', issue.title)[:50]
        filename = f"{issue.issue_id}_{safe_title.replace(' ', '_')}.md"
        content += f"- [{issue.issue_id}](./{filename}) - {issue.title}\n"

    content += """
---
*このサマリーは agent-Investigate によって自動生成されました*
"""

    filepath.write_text(content, encoding="utf-8")
    return filepath


async def investigate_all_issues(issues: list[Issue]) -> list[Issue]:
    """全イシューを調査"""
    console.print(Panel.fit(
        f"[bold blue]イシュー調査開始[/bold blue]\n"
        f"イシュー数: {len(issues)}\n"
        f"レポート出力先: {DOCS_DIR}",
        title="agent-Investigate"
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for i, issue in enumerate(issues):
            task = progress.add_task(
                f"[cyan][{i+1}/{len(issues)}][/cyan] {issue.issue_id}: {issue.title[:30]}...",
                total=1
            )

            await investigate_issue(issue)

            # レポートを保存
            report_path = save_investigation_report(issue, DOCS_DIR)

            status_icon = {
                "resolved": "[green]✓[/green]",
                "investigated": "[yellow]![/yellow]",
                "needs_more_investigation": "[yellow]?[/yellow]",
                "unknown": "[red]?[/red]",
                "error": "[red]✗[/red]"
            }.get(issue.status, "?")

            progress.update(task, description=f"{status_icon} {issue.title[:40]}")
            progress.advance(task)

    # サマリーを保存
    save_summary_report(issues, DOCS_DIR)

    return issues


def print_results(issues: list[Issue]):
    """調査結果を表示"""
    table = Table(title="調査結果")
    table.add_column("ID", style="cyan")
    table.add_column("タイトル", style="white", max_width=40)
    table.add_column("カテゴリ", style="blue")
    table.add_column("ステータス", style="bold")

    for issue in issues:
        status_style = {
            "resolved": "[green]解決済み[/green]",
            "investigated": "[yellow]調査済み[/yellow]",
            "needs_more_investigation": "[yellow]要追加調査[/yellow]",
            "unknown": "[red]不明[/red]",
            "error": "[red]エラー[/red]"
        }.get(issue.status, issue.status)

        table.add_row(
            issue.issue_id,
            issue.title[:40] + "..." if len(issue.title) > 40 else issue.title,
            issue.category,
            status_style
        )

    console.print(table)

    resolved = len([i for i in issues if i.status == "resolved"])
    console.print(Panel(
        f"[green]解決済み: {resolved}[/green] | "
        f"合計: {len(issues)}\n"
        f"レポート: {DOCS_DIR}/_SUMMARY.md",
        title="サマリー"
    ))


def show_issue_list(issues: list[Issue]):
    """イシュー一覧を表示"""
    table = Table(title="イシュー一覧")
    table.add_column("ID", style="cyan")
    table.add_column("タイトル", style="white")
    table.add_column("カテゴリ", style="blue")
    table.add_column("タイプ", style="dim")

    for issue in issues:
        table.add_row(
            issue.issue_id,
            issue.title,
            issue.category,
            issue.issue_type
        )

    console.print(table)


async def investigate_single_issue(issue_id: str, issues: list[Issue]) -> Optional[Issue]:
    """単一のイシューを調査"""
    target = next((i for i in issues if i.issue_id == issue_id), None)

    if not target:
        console.print(f"[red]イシューが見つかりません: {issue_id}[/red]")
        return None

    console.print(Panel.fit(
        f"[bold blue]イシュー調査[/bold blue]\n"
        f"ID: {target.issue_id}\n"
        f"タイトル: {target.title}",
        title="agent-Investigate"
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"調査中: {target.title[:40]}...", total=1)

        await investigate_issue(target)

        report_path = save_investigation_report(target, DOCS_DIR)

        progress.update(task, description=f"完了: {target.title[:40]}")
        progress.advance(task)

    console.print(f"\n[green]レポート保存先: {report_path}[/green]")
    console.print("\n[bold]調査結果:[/bold]")
    console.print(Markdown(target.investigation[:2000] if target.investigation else "なし"))

    return target


def main():
    """メインエントリポイント"""
    import argparse

    parser = argparse.ArgumentParser(
        description="UrawaCupイシュー調査エージェント（調査結果をドキュメント化）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python agent_investigate.py              # 全イシューを調査
  python agent_investigate.py --list       # イシュー一覧表示
  python agent_investigate.py -i T004      # 特定のイシューを調査
  python agent_investigate.py --reports    # 調査レポート一覧表示

調査レポートは D:/UrawaCup/docs/investigations/ に保存されます。
"""
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="イシュー一覧を表示"
    )
    parser.add_argument(
        "-i", "--issue",
        type=str,
        help="特定のイシューIDを調査"
    )
    parser.add_argument(
        "--reports",
        action="store_true",
        help="既存の調査レポート一覧を表示"
    )

    args = parser.parse_args()

    # イシューファイルを確認
    if not ISSUES_FILE.exists():
        console.print(f"[yellow]イシューファイルがありません: {ISSUES_FILE}[/yellow]")
        console.print("先に agent_check.py を実行してイシューを検出してください。")
        return

    # イシューをパース
    issues = parse_issues_file(ISSUES_FILE)

    if not issues:
        console.print("[yellow]調査対象のイシューがありません[/yellow]")
        return

    if args.list:
        show_issue_list(issues)
        return

    if args.reports:
        if not DOCS_DIR.exists():
            console.print("[yellow]調査レポートがありません[/yellow]")
            return

        table = Table(title="調査レポート一覧")
        table.add_column("ファイル", style="cyan")
        table.add_column("更新日時", style="dim")

        for f in sorted(DOCS_DIR.glob("*.md")):
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            table.add_row(f.name, mtime.strftime('%Y-%m-%d %H:%M'))

        console.print(table)
        return

    if args.issue:
        try:
            asyncio.run(investigate_single_issue(args.issue, issues))
        except KeyboardInterrupt:
            console.print("\n[yellow]調査中断[/yellow]")
        return

    # 全イシュー調査
    try:
        investigated = asyncio.run(investigate_all_issues(issues))
        print_results(investigated)
    except KeyboardInterrupt:
        console.print("\n[yellow]調査中断[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
