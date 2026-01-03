"""
アーキテクチャ検証エージェント
SystemDesign_v2.mdに基づいてコードベースを検証
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    ARCHITECTURE_RULES,
    FRONTEND_SRC_PATH,
    DEPRECATED_FILES,
)


@dataclass
class Violation:
    """アーキテクチャ違反"""
    rule_id: str
    rule: str
    severity: str
    location: str
    description: str
    fix: str
    line_number: Optional[int] = None


@dataclass
class ValidationResult:
    """検証結果"""
    status: str  # "pass" | "fail"
    violations: List[Violation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checked_files: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "rule": v.rule,
                    "severity": v.severity,
                    "location": v.location,
                    "description": v.description,
                    "fix": v.fix,
                    "line_number": v.line_number,
                }
                for v in self.violations
            ],
            "warnings": self.warnings,
            "checked_files": self.checked_files,
        }


class ArchitectureValidator:
    """アーキテクチャ検証エージェント"""

    def __init__(self, frontend_src_path: Path = None):
        self.src_path = frontend_src_path or FRONTEND_SRC_PATH
        self.rules = ARCHITECTURE_RULES
        self.deprecated_files = DEPRECATED_FILES

    def validate(self) -> ValidationResult:
        """全検証を実行"""
        result = ValidationResult(status="pass")

        # 1. 非推奨ファイルの存在チェック
        self._check_deprecated_files(result)

        # 2. 必須ファイルの存在チェック
        self._check_required_files(result)

        # 3. 禁止パターンのチェック
        self._check_forbidden_patterns(result)

        # 4. HTTPクライアントの使用状況チェック
        self._check_http_client_usage(result)

        # 5. 認証パターンのチェック
        self._check_auth_patterns(result)

        # ステータス判定
        if any(v.severity == "critical" for v in result.violations):
            result.status = "fail"
        elif len(result.violations) > 0:
            result.status = "warning"

        return result

    def _check_deprecated_files(self, result: ValidationResult):
        """非推奨ファイルの存在チェック"""
        for deprecated in self.deprecated_files:
            file_path = self.src_path / deprecated
            if file_path.exists():
                result.violations.append(Violation(
                    rule_id="ARCH-001",
                    rule="single_http_client",
                    severity="critical",
                    location=str(deprecated),
                    description=f"非推奨ファイル '{deprecated}' が存在します",
                    fix="このファイルを削除し、core/http/client.ts を使用してください",
                ))

    def _check_required_files(self, result: ValidationResult):
        """必須ファイルの存在チェック"""
        for rule_name, rule_config in self.rules.items():
            if "required_files" not in rule_config:
                continue

            for required_file in rule_config["required_files"]:
                file_path = self.src_path / required_file
                if not file_path.exists():
                    result.violations.append(Violation(
                        rule_id=rule_config.get("id", "UNKNOWN"),
                        rule=rule_name,
                        severity=rule_config.get("severity", "medium"),
                        location=str(required_file),
                        description=f"必須ファイル '{required_file}' が存在しません",
                        fix=rule_config.get("fix", "ファイルを作成してください"),
                    ))

    def _check_forbidden_patterns(self, result: ValidationResult):
        """禁止パターンのチェック"""
        ts_files = list(self.src_path.rglob("*.ts"))
        ts_files.extend(self.src_path.rglob("*.tsx"))
        result.checked_files = len(ts_files)

        for rule_name, rule_config in self.rules.items():
            if "forbidden_patterns" not in rule_config:
                continue

            for ts_file in ts_files:
                # core/ ディレクトリ内は除外
                if "core" in str(ts_file.relative_to(self.src_path)).split(os.sep):
                    continue

                try:
                    content = ts_file.read_text(encoding="utf-8")
                except Exception:
                    continue

                for pattern in rule_config["forbidden_patterns"]:
                    # ファイル名パターンの場合
                    if "/" in pattern and pattern.endswith(".ts"):
                        continue  # deprecated_files でチェック済み

                    # コードパターンの場合
                    matches = list(re.finditer(pattern, content))
                    for match in matches:
                        line_num = content[:match.start()].count("\n") + 1
                        result.violations.append(Violation(
                            rule_id=rule_config.get("id", "UNKNOWN"),
                            rule=rule_name,
                            severity=rule_config.get("severity", "medium"),
                            location=str(ts_file.relative_to(self.src_path)),
                            description=f"禁止パターン '{pattern}' が検出されました",
                            fix=rule_config.get("fix", "パターンを修正してください"),
                            line_number=line_num,
                        ))

    def _check_http_client_usage(self, result: ValidationResult):
        """HTTPクライアントの使用状況チェック"""
        # features/ ディレクトリ内の api.ts をチェック
        features_path = self.src_path / "features"
        if not features_path.exists():
            result.warnings.append("features/ ディレクトリが存在しません")
            return

        for api_file in features_path.rglob("api.ts"):
            try:
                content = api_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # httpClient のインポートチェック
            if "from '@/core/http'" not in content and "from '../core/http'" not in content:
                result.violations.append(Violation(
                    rule_id="ARCH-001",
                    rule="single_http_client",
                    severity="critical",
                    location=str(api_file.relative_to(self.src_path)),
                    description="httpClient を core/http からインポートしていません",
                    fix="import { httpClient } from '@/core/http' を追加してください",
                ))

    def _check_auth_patterns(self, result: ValidationResult):
        """認証パターンのチェック"""
        # localStorage 直接アクセスのチェック
        ts_files = list(self.src_path.rglob("*.ts"))
        ts_files.extend(self.src_path.rglob("*.tsx"))

        for ts_file in ts_files:
            # core/auth 内は除外
            relative_path = str(ts_file.relative_to(self.src_path))
            if relative_path.startswith("core/auth") or relative_path.startswith("core\\auth"):
                continue

            try:
                content = ts_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # localStorage トークンアクセスパターン
            token_patterns = [
                r"localStorage\.getItem\(['\"].*token",
                r"localStorage\.setItem\(['\"].*token",
            ]

            for pattern in token_patterns:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                for match in matches:
                    line_num = content[:match.start()].count("\n") + 1
                    result.violations.append(Violation(
                        rule_id="ARCH-002",
                        rule="centralized_auth",
                        severity="critical",
                        location=relative_path,
                        description="localStorage でトークンに直接アクセスしています",
                        fix="AuthManager を使用してトークンにアクセスしてください",
                        line_number=line_num,
                    ))

    def generate_report(self, result: ValidationResult) -> str:
        """検証レポートを生成"""
        lines = [
            "# アーキテクチャ検証レポート",
            "",
            f"## ステータス: {result.status.upper()}",
            f"- 検証ファイル数: {result.checked_files}",
            f"- 違反数: {len(result.violations)}",
            f"- 警告数: {len(result.warnings)}",
            "",
        ]

        if result.violations:
            lines.append("## 違反一覧")
            lines.append("")

            # 重要度でグループ化
            critical = [v for v in result.violations if v.severity == "critical"]
            high = [v for v in result.violations if v.severity == "high"]
            medium = [v for v in result.violations if v.severity == "medium"]

            if critical:
                lines.append("### Critical（要修正）")
                for v in critical:
                    lines.append(f"- **[{v.rule_id}]** `{v.location}`")
                    lines.append(f"  - {v.description}")
                    lines.append(f"  - 修正方法: {v.fix}")
                    if v.line_number:
                        lines.append(f"  - 行番号: {v.line_number}")
                lines.append("")

            if high:
                lines.append("### High（推奨修正）")
                for v in high:
                    lines.append(f"- **[{v.rule_id}]** `{v.location}`")
                    lines.append(f"  - {v.description}")
                    lines.append(f"  - 修正方法: {v.fix}")
                lines.append("")

            if medium:
                lines.append("### Medium（検討）")
                for v in medium:
                    lines.append(f"- **[{v.rule_id}]** `{v.location}`")
                    lines.append(f"  - {v.description}")
                lines.append("")

        if result.warnings:
            lines.append("## 警告")
            for w in result.warnings:
                lines.append(f"- {w}")
            lines.append("")

        return "\n".join(lines)


if __name__ == "__main__":
    # テスト実行
    validator = ArchitectureValidator()
    result = validator.validate()
    print(validator.generate_report(result))
