"""
浦和カップ 自動構築エージェント - インタラクティブ実行スクリプト

使い方:
  python run.py              # インタラクティブモード
  python run.py --all        # 全タスク自動実行
  python run.py --task 01    # 特定タスク実行
"""

import asyncio
import sys
from pathlib import Path

# リッチな出力のためのライブラリ（なければ標準出力）
try:
    from rich.console import Console
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from main import UrawaCupAgentBuilder


def print_header():
    """ヘッダー表示"""
    header = """
╔═══════════════════════════════════════════════════════════════╗
║     浦和カップ トーナメント管理システム 自動構築エージェント      ║
║                    Claude Agent SDK 使用                       ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(header)


def print_tasks(tasks: list):
    """タスク一覧表示"""
    if RICH_AVAILABLE:
        console = Console()
        table = Table(title="構築タスク一覧")
        table.add_column("ID", style="cyan")
        table.add_column("タスク名", style="green")
        table.add_column("優先度", style="yellow")

        for task in tasks:
            priority_color = {
                "最高": "[red]最高[/red]",
                "高": "[yellow]高[/yellow]",
                "中": "[blue]中[/blue]",
                "低": "[dim]低[/dim]"
            }.get(task["priority"], task["priority"])

            table.add_row(task["id"], task["name"], priority_color)

        console.print(table)
    else:
        print("\n構築タスク一覧:")
        print("-" * 60)
        for task in tasks:
            print(f"  {task['id']}: {task['name']} (優先度: {task['priority']})")
        print("-" * 60)


def get_user_choice(tasks: list) -> str:
    """ユーザーの選択を取得"""
    if RICH_AVAILABLE:
        console = Console()
        console.print("\n[bold]実行オプション:[/bold]")
        console.print("  [cyan]all[/cyan]     - 全タスクを順番に実行")
        console.print("  [cyan]<ID>[/cyan]    - 特定のタスクを実行 (例: 01_project_setup)")
        console.print("  [cyan]from <ID>[/cyan] - 指定タスクから最後まで実行")
        console.print("  [cyan]q[/cyan]       - 終了")

        choice = Prompt.ask("\n選択", default="all")
    else:
        print("\n実行オプション:")
        print("  all      - 全タスクを順番に実行")
        print("  <ID>     - 特定のタスクを実行 (例: 01_project_setup)")
        print("  from <ID> - 指定タスクから最後まで実行")
        print("  q        - 終了")

        choice = input("\n選択 [all]: ").strip() or "all"

    return choice


async def interactive_mode():
    """インタラクティブモード"""
    print_header()

    builder = UrawaCupAgentBuilder()
    print_tasks(builder.tasks)

    while True:
        choice = get_user_choice(builder.tasks)

        if choice.lower() == "q":
            print("\n終了します。")
            break

        elif choice.lower() == "all":
            if RICH_AVAILABLE:
                if not Confirm.ask("全タスクを実行しますか？"):
                    continue
            else:
                confirm = input("全タスクを実行しますか？ (y/n): ")
                if confirm.lower() != "y":
                    continue

            await builder.run_all_tasks()

        elif choice.lower().startswith("from "):
            task_id = choice[5:].strip()
            await builder.run_all_tasks(start_from=task_id)

        else:
            # 特定タスクの実行
            task_id = choice.strip()
            try:
                await builder.run_single_task(task_id)
            except ValueError as e:
                print(f"エラー: {e}")

        print("\n" + "=" * 60)
        continue_choice = input("続けますか？ (y/n): ")
        if continue_choice.lower() != "y":
            break


async def run_all():
    """全タスク自動実行"""
    print_header()
    builder = UrawaCupAgentBuilder()
    await builder.run_all_tasks()


async def run_task(task_id: str):
    """特定タスク実行"""
    print_header()
    builder = UrawaCupAgentBuilder()
    await builder.run_single_task(task_id)


def main():
    """エントリーポイント"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            asyncio.run(run_all())
        elif sys.argv[1] == "--task" and len(sys.argv) > 2:
            asyncio.run(run_task(sys.argv[2]))
        elif sys.argv[1] == "--help":
            print(__doc__)
        else:
            print("不明なオプション。--help で使い方を確認してください。")
    else:
        asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()
