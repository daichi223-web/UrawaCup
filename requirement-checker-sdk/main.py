"""
UrawaCup 要件チェックSDK - メインスクリプト
Claude Agent SDKを使用して要件の実装状況をチェックする
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.requirements_data import (
    Phase,
    Priority,
    ALL_REQUIREMENTS,
    get_requirements_by_phase,
    get_all_categories,
)
from src.code_checker import (
    CodeChecker,
    CheckResult,
    CheckSummary,
    format_check_result,
    format_summary,
    ImplementationStatus,
)


class RequirementChecker:
    """要件チェッカーの主要クラス"""

    def __init__(self, project_root: str = None):
        if project_root is None:
            # デフォルトはUrawaCupプロジェクトルート
            # Windows環境でのパス問題を回避
            script_dir = Path(__file__).resolve().parent
            project_root = str(script_dir.parent)
            # パスが正しくない場合はD:\UrawaCupを使用
            if not (Path(project_root) / "src").exists():
                project_root = "D:/UrawaCup"
        self.project_root = Path(project_root)
        self.checker = CodeChecker(str(self.project_root))

    def run_full_check(self) -> dict:
        """全要件のチェックを実行"""
        print("=" * 60)
        print("UrawaCup 要件実装状況チェック")
        print(f"プロジェクトルート: {self.project_root}")
        print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        summary = self.checker.check_all_requirements()
        print(format_summary(summary))

        return self._summary_to_dict(summary)

    def run_phase_check(self, phase: Phase) -> dict:
        """フェーズ別チェックを実行"""
        print(f"\n{'=' * 60}")
        print(f"Phase {phase.value} 要件チェック")
        print("=" * 60)

        summary = self.checker.check_by_phase(phase)
        print(format_summary(summary))

        print("\n--- 詳細結果 ---")
        for result in summary.results:
            print(format_check_result(result))
            print()

        return self._summary_to_dict(summary)

    def run_priority_check(self, priority: Priority) -> dict:
        """優先度別チェックを実行"""
        print(f"\n{'=' * 60}")
        print(f"優先度「{priority.value}」の要件チェック")
        print("=" * 60)

        summary = self.checker.check_by_priority(priority)
        print(format_summary(summary))

        return self._summary_to_dict(summary)

    def get_not_implemented(self) -> list[CheckResult]:
        """未実装要件を取得"""
        summary = self.checker.check_all_requirements()
        return [r for r in summary.results if r.status == ImplementationStatus.NOT_STARTED]

    def get_partially_implemented(self) -> list[CheckResult]:
        """部分実装要件を取得"""
        summary = self.checker.check_all_requirements()
        return [r for r in summary.results if r.status == ImplementationStatus.PARTIAL]

    def generate_report(self, output_path: str = None) -> str:
        """詳細レポートを生成"""
        if output_path is None:
            output_path = str(self.project_root / "requirement-checker-sdk" / "reports")

        Path(output_path).mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path(output_path) / f"requirement_check_{timestamp}.md"

        summary = self.checker.check_all_requirements()

        lines = [
            "# UrawaCup 要件実装状況レポート",
            "",
            f"**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**プロジェクトルート**: {self.project_root}",
            "",
            "## 概要",
            "",
            f"| 項目 | 件数 | 割合 |",
            f"|------|------|------|",
            f"| 総要件数 | {summary.total_requirements} | 100% |",
            f"| 完了 | {summary.completed} | {summary.completed / summary.total_requirements * 100:.1f}% |",
            f"| 部分実装 | {summary.partial} | {summary.partial / summary.total_requirements * 100:.1f}% |",
            f"| 実装中 | {summary.in_progress} | {summary.in_progress / summary.total_requirements * 100:.1f}% |",
            f"| 未着手 | {summary.not_started} | {summary.not_started / summary.total_requirements * 100:.1f}% |",
            "",
            f"**実装率**: {summary.completion_rate:.1f}%",
            "",
        ]

        # フェーズ別サマリー
        for phase in [Phase.MINI, Phase.MIDDLE, Phase.MAX]:
            phase_summary = self.checker.check_by_phase(phase)
            lines.extend([
                f"### Phase {phase.value}",
                "",
                f"- 完了: {phase_summary.completed}/{phase_summary.total_requirements}",
                f"- 実装率: {phase_summary.completion_rate:.1f}%",
                "",
            ])

        # 詳細結果
        lines.extend([
            "## 詳細結果",
            "",
        ])

        status_order = [
            ImplementationStatus.NOT_STARTED,
            ImplementationStatus.IN_PROGRESS,
            ImplementationStatus.PARTIAL,
            ImplementationStatus.COMPLETED,
        ]

        status_labels = {
            ImplementationStatus.COMPLETED: "完了",
            ImplementationStatus.PARTIAL: "部分実装",
            ImplementationStatus.IN_PROGRESS: "実装中",
            ImplementationStatus.NOT_STARTED: "未着手",
        }

        for status in status_order:
            status_results = [r for r in summary.results if r.status == status]
            if status_results:
                lines.extend([
                    f"### {status_labels[status]}",
                    "",
                ])
                for result in status_results:
                    lines.extend([
                        f"#### {result.requirement.id}: {result.requirement.name}",
                        "",
                        f"- **説明**: {result.requirement.description}",
                        f"- **フェーズ**: {result.requirement.phase.value}",
                        f"- **優先度**: {result.requirement.priority.value}",
                        f"- **カテゴリ**: {result.requirement.category}",
                    ])
                    if result.matched_files:
                        lines.append(f"- **関連ファイル**: {', '.join(result.matched_files[:10])}")
                    lines.append("")

        report_content = "\n".join(lines)

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"レポートを生成しました: {report_file}")
        return str(report_file)

    def generate_issues(self) -> list[dict]:
        """未実装・問題のある要件をIssue形式で出力"""
        summary = self.checker.check_all_requirements()
        issues = []

        for result in summary.results:
            if result.status in [ImplementationStatus.NOT_STARTED, ImplementationStatus.PARTIAL]:
                issue = {
                    "id": result.requirement.id,
                    "title": f"[{result.requirement.phase.value}] {result.requirement.name}",
                    "description": result.requirement.description,
                    "status": result.status.value,
                    "priority": result.requirement.priority.value,
                    "category": result.requirement.category,
                    "matched_files": result.matched_files,
                }
                issues.append(issue)

        return issues

    def _summary_to_dict(self, summary: CheckSummary) -> dict:
        """サマリーを辞書に変換"""
        return {
            "total": summary.total_requirements,
            "completed": summary.completed,
            "partial": summary.partial,
            "in_progress": summary.in_progress,
            "not_started": summary.not_started,
            "completion_rate": summary.completion_rate,
        }


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="UrawaCup 要件チェックSDK")
    parser.add_argument("--project", "-p", type=str, help="プロジェクトルートパス")
    parser.add_argument("--phase", choices=["MINI", "MIDDLE", "MAX"], help="チェック対象フェーズ")
    parser.add_argument("--priority", choices=["最高", "高", "中", "低"], help="チェック対象優先度")
    parser.add_argument("--report", "-r", action="store_true", help="レポートを生成")
    parser.add_argument("--issues", "-i", action="store_true", help="Issue一覧を出力")

    args = parser.parse_args()

    checker = RequirementChecker(args.project)

    if args.phase:
        phase = Phase[args.phase]
        checker.run_phase_check(phase)
    elif args.priority:
        priority_map = {"最高": Priority.HIGHEST, "高": Priority.HIGH, "中": Priority.MEDIUM, "低": Priority.LOW}
        priority = priority_map[args.priority]
        checker.run_priority_check(priority)
    else:
        checker.run_full_check()

    if args.report:
        checker.generate_report()

    if args.issues:
        issues = checker.generate_issues()
        print("\n--- 未実装/問題のある要件 ---")
        for issue in issues:
            print(f"[{issue['priority']}] {issue['title']}: {issue['status']}")


if __name__ == "__main__":
    main()
