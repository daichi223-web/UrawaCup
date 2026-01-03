#!/usr/bin/env python3
"""
agent-Fix: UrawaCup自動修正エージェント
調査レポートを読み取り、実装を要件と比較し、修正可能なものは自動修正する
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
from rich.prompt import Confirm

console = Console()

# パス設定
PROJECT_ROOT = Path("D:/UrawaCup")
ISSUES_FILE = PROJECT_ROOT / "ISSUES.md"
DOCS_DIR = PROJECT_ROOT / "docs"
INVESTIGATIONS_DIR = DOCS_DIR / "investigations"
SRC_DIR = PROJECT_ROOT / "src"


class FixResult:
    """修正結果を格納するクラス"""
    def __init__(self, issue_id: str, title: str):
        self.issue_id = issue_id
        self.title = title
        self.status: str = "pending"  # pending, fixed, skipped, failed, needs_manual
        self.changes: list[str] = []
        self.new_issues: list[str] = []
        self.explanation: str = ""


def load_investigation_reports() -> dict[str, str]:
    """調査レポートを読み込む"""
    reports = {}

    if not INVESTIGATIONS_DIR.exists():
        return reports

    for filepath in INVESTIGATIONS_DIR.glob("*.md"):
        if filepath.name == "_SUMMARY.md":
            continue
        content = filepath.read_text(encoding="utf-8")
        # イシューIDを抽出
        match = re.search(r'\[([A-Z]\d+)\]', filepath.name)
        if match:
            reports[match.group(1)] = content

    return reports


def load_issues_file() -> str:
    """ISSUES.mdを読み込む"""
    if ISSUES_FILE.exists():
        return ISSUES_FILE.read_text(encoding="utf-8")
    return ""


def append_issue(issue_id: str, title: str, category: str,
                 issue_type: str, test_name: str, details: str):
    """新しいイシューをISSUES.mdに追記"""
    icon_map = {
        "BUG": "🐛",
        "QUESTION": "❓",
        "IMPROVEMENT": "💡",
        "ERROR": "❌",
        "NOTE": "📝"
    }
    icon = icon_map.get(issue_type, "📝")

    entry = f"""

### {icon} [{issue_id}] {title}

- **カテゴリ**: {category}
- **テスト**: {test_name}
- **タイプ**: {issue_type}
- **検出日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{details}

---
"""

    if ISSUES_FILE.exists():
        current = ISSUES_FILE.read_text(encoding="utf-8")
    else:
        current = "# UrawaCup イシュー一覧\n\n自動検出されたイシューの一覧です。\n"

    ISSUES_FILE.write_text(current + entry, encoding="utf-8")


def get_next_issue_id() -> str:
    """次のイシューIDを生成"""
    if not ISSUES_FILE.exists():
        return "F001"

    content = ISSUES_FILE.read_text(encoding="utf-8")
    matches = re.findall(r'\[F(\d+)\]', content)

    if not matches:
        return "F001"

    max_num = max(int(m) for m in matches)
    return f"F{max_num + 1:03d}"


async def analyze_and_fix(report_content: str, issue_id: str,
                          dry_run: bool = False) -> FixResult:
    """レポートを分析し、修正を試みる"""

    result = FixResult(issue_id, "")

    prompt = f"""
以下の調査レポートを分析し、修正を実行してください。

## 調査レポート
{report_content}

## あなたのタスク

1. **現状分析**: 調査レポートの内容を理解し、問題点を特定してください

2. **要件との比較**:
   - 期待される動作は何か
   - 現在の実装はどうなっているか
   - ギャップは何か

3. **修正判断**:
   - 自動修正可能か判断してください
   - 修正可能な場合は修正を実行してください
   - 修正不可能な場合は理由を説明してください

4. **修正実行** (dry_run={dry_run}の場合は実行しない):
   - ファイルを読んで問題箇所を特定
   - 必要な修正を適用
   - 修正後の動作確認（可能な場合）

5. **新たな不明点があれば報告**:
   - 調査中に見つかった新しい問題
   - 追加調査が必要な事項

## 出力形式

### 分析結果
（問題の要約と根本原因）

### 修正判断
- 自動修正可能: [YES/NO]
- 理由: （理由の説明）

### 修正内容
（修正した場合の詳細、または修正できない理由）

### 変更ファイル
（修正したファイルのリスト）

### 新たな不明点
（あれば記載）

### ステータス
[FIXED / SKIPPED / NEEDS_MANUAL / FAILED]
"""

    full_response = []

    try:
        tools = ["Read", "Grep", "Glob"]
        if not dry_run:
            tools.extend(["Edit", "Write", "Bash"])

        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                allowed_tools=tools,
                max_turns=30,
            )
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if hasattr(block, "text"):
                        full_response.append(block.text)

        result.explanation = "\n".join(full_response)

        # ステータスを抽出
        explanation_lower = result.explanation.lower()
        if "fixed" in explanation_lower or "修正完了" in explanation_lower:
            result.status = "fixed"
        elif "skipped" in explanation_lower or "スキップ" in explanation_lower:
            result.status = "skipped"
        elif "needs_manual" in explanation_lower or "手動" in explanation_lower:
            result.status = "needs_manual"
        elif "failed" in explanation_lower or "失敗" in explanation_lower:
            result.status = "failed"
        else:
            result.status = "analyzed"

        # 変更ファイルを抽出
        change_section = re.search(r'### 変更ファイル\n(.*?)(?=###|\Z)',
                                   result.explanation, re.DOTALL)
        if change_section:
            files = re.findall(r'[-*]\s*(.+\.(?:py|tsx?|js|json|md))',
                              change_section.group(1))
            result.changes = files

        # 新たな不明点を抽出してイシュー化
        unknown_section = re.search(r'### 新たな不明点\n(.*?)(?=###|\Z)',
                                    result.explanation, re.DOTALL)
        if unknown_section:
            unknown_text = unknown_section.group(1).strip()
            if unknown_text and unknown_text.lower() not in ["なし", "none", "特になし", "-"]:
                new_issue_id = get_next_issue_id()
                append_issue(
                    issue_id=new_issue_id,
                    title=f"agent-Fix発見: {issue_id}関連の追加調査事項",
                    category="auto-fix",
                    issue_type="QUESTION",
                    test_name=f"agent-Fix ({issue_id})",
                    details=f"## 元イシュー\n{issue_id}\n\n## 新たな不明点\n{unknown_text}"
                )
                result.new_issues.append(new_issue_id)

    except Exception as e:
        result.explanation = f"修正中にエラーが発生: {str(e)}"
        result.status = "failed"

    return result


def save_fix_report(results: list[FixResult]) -> Path:
    """修正レポートを保存"""
    report_dir = DOCS_DIR / "fixes"
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = report_dir / f"fix_report_{timestamp}.md"

    fixed = [r for r in results if r.status == "fixed"]
    needs_manual = [r for r in results if r.status == "needs_manual"]
    failed = [r for r in results if r.status == "failed"]

    content = f"""# 自動修正レポート

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 統計

| ステータス | 件数 |
|-----------|------|
| 修正完了 | {len(fixed)} |
| 手動対応必要 | {len(needs_manual)} |
| 失敗 | {len(failed)} |
| **合計** | **{len(results)}** |

## 修正完了

"""

    for r in fixed:
        content += f"### [{r.issue_id}] {r.title}\n\n"
        if r.changes:
            content += "変更ファイル:\n"
            for f in r.changes:
                content += f"- {f}\n"
        content += "\n"

    content += "## 手動対応必要\n\n"

    for r in needs_manual:
        content += f"### [{r.issue_id}] {r.title}\n\n"
        content += f"{r.explanation[:500]}...\n\n" if len(r.explanation) > 500 else f"{r.explanation}\n\n"

    content += "## 失敗\n\n"

    for r in failed:
        content += f"### [{r.issue_id}] {r.title}\n\n"
        content += f"{r.explanation[:300]}...\n\n" if len(r.explanation) > 300 else f"{r.explanation}\n\n"

    content += """
---
*このレポートは agent-Fix によって自動生成されました*
"""

    filepath.write_text(content, encoding="utf-8")
    return filepath


async def run_fix_process(issue_ids: Optional[list[str]] = None,
                          dry_run: bool = False):
    """修正プロセスを実行"""

    # 調査レポートを読み込み
    reports = load_investigation_reports()

    if not reports:
        console.print("[yellow]調査レポートがありません[/yellow]")
        console.print("先に agent_investigate.py を実行してください。")
        return

    # 対象を絞り込み
    if issue_ids:
        reports = {k: v for k, v in reports.items() if k in issue_ids}

    if not reports:
        console.print("[yellow]対象のレポートがありません[/yellow]")
        return

    mode = "[DRY-RUN]" if dry_run else "[LIVE]"
    console.print(Panel.fit(
        f"[bold blue]自動修正開始 {mode}[/bold blue]\n"
        f"対象イシュー数: {len(reports)}\n"
        f"調査レポート: {INVESTIGATIONS_DIR}",
        title="agent-Fix"
    ))

    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for i, (issue_id, content) in enumerate(reports.items()):
            task = progress.add_task(
                f"[cyan][{i+1}/{len(reports)}][/cyan] {issue_id}: 分析・修正中...",
                total=1
            )

            result = await analyze_and_fix(content, issue_id, dry_run)
            result.title = issue_id  # タイトルをセット
            results.append(result)

            status_icon = {
                "fixed": "[green]✓[/green]",
                "skipped": "[dim]○[/dim]",
                "needs_manual": "[yellow]![/yellow]",
                "failed": "[red]✗[/red]",
                "analyzed": "[blue]?[/blue]"
            }.get(result.status, "?")

            progress.update(task, description=f"{status_icon} {issue_id}")
            progress.advance(task)

    # レポートを保存
    report_path = save_fix_report(results)

    # 結果を表示
    print_results(results, report_path)


def print_results(results: list[FixResult], report_path: Path):
    """結果を表示"""
    table = Table(title="修正結果")
    table.add_column("ID", style="cyan")
    table.add_column("ステータス", style="bold")
    table.add_column("変更ファイル数", style="dim")
    table.add_column("新規イシュー", style="yellow")

    for r in results:
        status_style = {
            "fixed": "[green]修正完了[/green]",
            "skipped": "[dim]スキップ[/dim]",
            "needs_manual": "[yellow]手動対応[/yellow]",
            "failed": "[red]失敗[/red]",
            "analyzed": "[blue]分析済み[/blue]"
        }.get(r.status, r.status)

        table.add_row(
            r.issue_id,
            status_style,
            str(len(r.changes)),
            ", ".join(r.new_issues) if r.new_issues else "-"
        )

    console.print(table)

    fixed = len([r for r in results if r.status == "fixed"])
    new_issues = sum(len(r.new_issues) for r in results)

    console.print(Panel(
        f"[green]修正完了: {fixed}[/green] | "
        f"合計: {len(results)} | "
        f"[yellow]新規イシュー: {new_issues}[/yellow]\n"
        f"レポート: {report_path}",
        title="サマリー"
    ))


async def compare_with_requirements():
    """要件との比較を実行"""

    prompt = """
UrawaCupプロジェクトの現在の実装を要件と比較してください。

## タスク

1. **ドキュメントを読む**:
   - D:/UrawaCup/docs/ 以下のドキュメントを確認
   - D:/UrawaCup/ISSUES.md を確認
   - D:/UrawaCup/docs/investigations/ の調査レポートを確認

2. **実装を確認**:
   - D:/UrawaCup/src/frontend/ のReactコード
   - D:/UrawaCup/src/backend/ のPythonコード

3. **要件との比較**:
   - ドキュメントに記載された要件
   - 調査レポートで特定された問題
   - 現在の実装状態

4. **ギャップ分析**:
   - 未実装の機能
   - バグが残っている箇所
   - 改善が必要な箇所

## 出力形式

### 要件サマリー
（主要な要件の一覧）

### 実装状況
| 要件 | 状態 | 備考 |
|------|------|------|
| ... | OK/NG/部分的 | ... |

### 未解決の問題
（まだ修正されていない問題のリスト）

### 推奨アクション
（優先順位付きの改善提案）
"""

    console.print(Panel.fit(
        "[bold blue]要件比較分析開始[/bold blue]\n"
        "ドキュメントと実装を比較します...",
        title="agent-Fix"
    ))

    full_response = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("分析中...", total=None)

        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                allowed_tools=["Read", "Grep", "Glob"],
                max_turns=30,
            )
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if hasattr(block, "text"):
                        full_response.append(block.text)

        progress.update(task, description="完了")

    # 結果を表示
    result_text = "\n".join(full_response)
    console.print("\n[bold]分析結果:[/bold]\n")
    console.print(Markdown(result_text[:5000] if len(result_text) > 5000 else result_text))

    # レポートを保存
    report_dir = DOCS_DIR / "fixes"
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = report_dir / f"requirements_comparison_{timestamp}.md"

    content = f"""# 要件比較レポート

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{result_text}

---
*このレポートは agent-Fix によって自動生成されました*
"""

    filepath.write_text(content, encoding="utf-8")
    console.print(f"\n[green]レポート保存先: {filepath}[/green]")


def main():
    """メインエントリポイント"""
    import argparse

    parser = argparse.ArgumentParser(
        description="UrawaCup自動修正エージェント（調査結果に基づき自動修正）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python agent_fix.py                    # 全イシューの修正を試行
  python agent_fix.py --dry-run          # 修正せずに分析のみ
  python agent_fix.py -i T004            # 特定のイシューを修正
  python agent_fix.py --compare          # 要件との比較分析

修正レポートは D:/UrawaCup/docs/fixes/ に保存されます。
"""
    )
    parser.add_argument(
        "-i", "--issue",
        type=str,
        nargs="+",
        help="特定のイシューIDを修正（複数指定可）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="修正せずに分析のみ実行"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="要件との比較分析を実行"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="調査レポート一覧を表示"
    )

    args = parser.parse_args()

    if args.list:
        reports = load_investigation_reports()
        if not reports:
            console.print("[yellow]調査レポートがありません[/yellow]")
            return

        table = Table(title="調査レポート一覧")
        table.add_column("ID", style="cyan")
        table.add_column("ファイル", style="white")

        for issue_id in sorted(reports.keys()):
            table.add_row(issue_id, f"{issue_id}_*.md")

        console.print(table)
        return

    if args.compare:
        try:
            asyncio.run(compare_with_requirements())
        except KeyboardInterrupt:
            console.print("\n[yellow]分析中断[/yellow]")
        return

    # 調査レポートの存在確認
    if not INVESTIGATIONS_DIR.exists() or not list(INVESTIGATIONS_DIR.glob("*.md")):
        console.print("[yellow]調査レポートがありません[/yellow]")
        console.print("先に agent_investigate.py を実行してください。")
        return

    try:
        asyncio.run(run_fix_process(args.issue, args.dry_run))
    except KeyboardInterrupt:
        console.print("\n[yellow]修正中断[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
