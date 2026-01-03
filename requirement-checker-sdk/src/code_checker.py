"""
コードベースチェッカー
要件定義に基づいてコードベースの実装状況をチェックする
"""

import os
import re
import glob
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from .requirements_data import (
    Requirement,
    ImplementationStatus,
    ALL_REQUIREMENTS,
    Phase,
    Priority,
)


@dataclass
class CheckResult:
    """チェック結果"""
    requirement: Requirement
    status: ImplementationStatus
    matched_files: list[str] = field(default_factory=list)
    matched_patterns: dict[str, list[str]] = field(default_factory=dict)  # pattern -> [file paths]
    notes: str = ""


@dataclass
class CheckSummary:
    """チェックサマリー"""
    total_requirements: int
    completed: int
    partial: int
    in_progress: int
    not_started: int
    results: list[CheckResult] = field(default_factory=list)

    @property
    def completion_rate(self) -> float:
        if self.total_requirements == 0:
            return 0.0
        return (self.completed + self.partial * 0.5) / self.total_requirements * 100


class CodeChecker:
    """コードベースの実装状況をチェックするクラス"""

    # 除外するディレクトリパターン
    EXCLUDE_DIRS = {'node_modules', '.git', '__pycache__', '.venv', 'venv', 'dist', 'build'}

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.src_path = self.project_root / "src"

    def _should_exclude(self, path: Path) -> bool:
        """除外すべきパスかどうか判定"""
        parts = path.parts
        return any(excluded in parts for excluded in self.EXCLUDE_DIRS)

    def _find_files(self, pattern: str) -> list[Path]:
        """globパターンでファイルを検索（除外ディレクトリをスキップ）"""
        search_path = str(self.src_path / pattern)
        files = [Path(p) for p in glob.glob(search_path, recursive=True)]
        return [f for f in files if not self._should_exclude(f)]

    def _search_pattern_in_file(self, file_path: Path, pattern: str) -> bool:
        """ファイル内でパターンを検索"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return bool(re.search(pattern, content, re.IGNORECASE))
        except Exception:
            return False

    def _search_pattern_in_all_files(self, pattern: str) -> list[str]:
        """すべてのソースファイルでパターンを検索"""
        matched_files = []

        # Python files
        for ext in ['**/*.py', '**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx']:
            for file_path in self._find_files(ext):
                if self._search_pattern_in_file(file_path, pattern):
                    matched_files.append(str(file_path.relative_to(self.project_root)))

        return matched_files

    def check_requirement(self, requirement: Requirement) -> CheckResult:
        """単一要件のチェック"""
        matched_files: set[str] = set()
        matched_patterns: dict[str, list[str]] = {}

        # パターンマッチング
        for pattern in requirement.check_patterns:
            files = self._search_pattern_in_all_files(pattern)
            if files:
                matched_patterns[pattern] = files
                matched_files.update(files)

        # ファイル存在チェック
        for file_pattern in requirement.check_files:
            found_files = self._find_files(file_pattern)
            for f in found_files:
                matched_files.add(str(f.relative_to(self.project_root)))

        # ステータス判定
        pattern_match_rate = len(matched_patterns) / len(requirement.check_patterns) if requirement.check_patterns else 0

        if pattern_match_rate >= 0.8:
            status = ImplementationStatus.COMPLETED
        elif pattern_match_rate >= 0.5:
            status = ImplementationStatus.PARTIAL
        elif pattern_match_rate > 0:
            status = ImplementationStatus.IN_PROGRESS
        else:
            status = ImplementationStatus.NOT_STARTED

        return CheckResult(
            requirement=requirement,
            status=status,
            matched_files=list(matched_files),
            matched_patterns=matched_patterns,
        )

    def check_all_requirements(self) -> CheckSummary:
        """全要件のチェック"""
        results = []

        for req in ALL_REQUIREMENTS:
            result = self.check_requirement(req)
            results.append(result)

        # サマリー計算
        completed = sum(1 for r in results if r.status == ImplementationStatus.COMPLETED)
        partial = sum(1 for r in results if r.status == ImplementationStatus.PARTIAL)
        in_progress = sum(1 for r in results if r.status == ImplementationStatus.IN_PROGRESS)
        not_started = sum(1 for r in results if r.status == ImplementationStatus.NOT_STARTED)

        return CheckSummary(
            total_requirements=len(results),
            completed=completed,
            partial=partial,
            in_progress=in_progress,
            not_started=not_started,
            results=results,
        )

    def check_by_phase(self, phase: Phase) -> CheckSummary:
        """フェーズ別のチェック"""
        phase_reqs = [r for r in ALL_REQUIREMENTS if r.phase == phase]
        results = [self.check_requirement(req) for req in phase_reqs]

        completed = sum(1 for r in results if r.status == ImplementationStatus.COMPLETED)
        partial = sum(1 for r in results if r.status == ImplementationStatus.PARTIAL)
        in_progress = sum(1 for r in results if r.status == ImplementationStatus.IN_PROGRESS)
        not_started = sum(1 for r in results if r.status == ImplementationStatus.NOT_STARTED)

        return CheckSummary(
            total_requirements=len(results),
            completed=completed,
            partial=partial,
            in_progress=in_progress,
            not_started=not_started,
            results=results,
        )

    def check_by_priority(self, priority: Priority) -> CheckSummary:
        """優先度別のチェック"""
        priority_reqs = [r for r in ALL_REQUIREMENTS if r.priority == priority]
        results = [self.check_requirement(req) for req in priority_reqs]

        completed = sum(1 for r in results if r.status == ImplementationStatus.COMPLETED)
        partial = sum(1 for r in results if r.status == ImplementationStatus.PARTIAL)
        in_progress = sum(1 for r in results if r.status == ImplementationStatus.IN_PROGRESS)
        not_started = sum(1 for r in results if r.status == ImplementationStatus.NOT_STARTED)

        return CheckSummary(
            total_requirements=len(results),
            completed=completed,
            partial=partial,
            in_progress=in_progress,
            not_started=not_started,
            results=results,
        )


def format_check_result(result: CheckResult) -> str:
    """チェック結果をフォーマット"""
    status_emoji = {
        ImplementationStatus.COMPLETED: "[完了]",
        ImplementationStatus.PARTIAL: "[部分]",
        ImplementationStatus.IN_PROGRESS: "[進行]",
        ImplementationStatus.NOT_STARTED: "[未着手]",
    }

    lines = [
        f"{status_emoji[result.status]} {result.requirement.id}: {result.requirement.name}",
        f"   説明: {result.requirement.description}",
        f"   フェーズ: {result.requirement.phase.value} | 優先度: {result.requirement.priority.value}",
    ]

    if result.matched_files:
        lines.append(f"   関連ファイル: {', '.join(result.matched_files[:5])}")
        if len(result.matched_files) > 5:
            lines.append(f"   ... 他 {len(result.matched_files) - 5} ファイル")

    return "\n".join(lines)


def format_summary(summary: CheckSummary) -> str:
    """サマリーをフォーマット"""
    lines = [
        "=" * 60,
        "要件実装状況サマリー",
        "=" * 60,
        f"総要件数: {summary.total_requirements}",
        f"完了: {summary.completed} ({summary.completed / summary.total_requirements * 100:.1f}%)",
        f"部分実装: {summary.partial} ({summary.partial / summary.total_requirements * 100:.1f}%)",
        f"実装中: {summary.in_progress} ({summary.in_progress / summary.total_requirements * 100:.1f}%)",
        f"未着手: {summary.not_started} ({summary.not_started / summary.total_requirements * 100:.1f}%)",
        f"実装率: {summary.completion_rate:.1f}%",
        "=" * 60,
    ]
    return "\n".join(lines)
