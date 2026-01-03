"""
Issue対応タスクのみを実行するスクリプト
"""

import asyncio
import sys
import os

# Windows環境でのUTF-8対応
os.environ['PYTHONIOENCODING'] = 'utf-8'

from main import UrawaCupAgentBuilder, TaskDefinition

# Issue対応タスクのIDリスト
ISSUE_TASK_IDS = [
    # 既存の完了済みIssue（スキップ可能）
    # "issue_007_finals_bracket",
    # "issue_008_approval_flow",
    # "issue_009_auth_permissions",
    # "issue_010_pwa",
    # "issue_011_realtime",
    # "issue_012_public_view",
    # 2026-01-01 新規Issue
    "issue_009a_secret_key",
    "issue_009b_camelcase",
    "issue_009c_admin_script",
    "issue_016_scorer_ranking_ui",
]


async def main():
    """Issueタスクのみ実行"""
    print("=" * 60)
    print("Issue対応タスク実行開始")
    print("=" * 60)

    builder = UrawaCupAgentBuilder()

    # Issueタスクのみをフィルタ
    issue_tasks = [t for t in builder.tasks if t["id"] in ISSUE_TASK_IDS]

    print(f"\n実行するタスク数: {len(issue_tasks)}")
    for task in issue_tasks:
        print(f"  - {task['name']}")
    print()

    for task in issue_tasks:
        print(f"\n{'='*60}")
        print(f"実行中: {task['name']}")
        print(f"{'='*60}\n")

        retries = 0
        max_retries = 2

        while retries < max_retries:
            result = await builder.run_task(task)

            if result["status"] == "completed":
                builder.completed_tasks.append(task["id"])
                print(f"\n✓ {task['name']} 完了\n")
                break
            else:
                retries += 1
                if retries < max_retries:
                    print(f"\n再試行 ({retries}/{max_retries})...\n")
                    await asyncio.sleep(2)
                else:
                    builder.failed_tasks.append(task["id"])
                    print(f"\n✗ {task['name']} 失敗（最大リトライ回数超過）\n")

    # 最終レポート
    print("\n" + "=" * 60)
    print("Issue対応タスク完了レポート")
    print("=" * 60)
    print(f"完了: {len(builder.completed_tasks)}/{len(issue_tasks)}")
    print(f"失敗: {len(builder.failed_tasks)}")

    for task in issue_tasks:
        if task["id"] in builder.completed_tasks:
            print(f"  ✓ {task['name']}")
        elif task["id"] in builder.failed_tasks:
            print(f"  ✗ {task['name']}")
        else:
            print(f"  - {task['name']}")


if __name__ == "__main__":
    asyncio.run(main())
