"""
浦和カップ SDK生成エージェント - 自動ループ
アーキテクチャ検証 → Issue作成 → コード生成 → 再検証のループを自動実行
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    LOG_DIR,
    OUTPUT_DIR,
    FEATURES,
    FRONTEND_SRC_PATH,
)
from .architecture_validator import ArchitectureValidator, ValidationResult
from .code_generator import CodeGenerator
from .issue_manager import IssueManager
from .requirement_analyzer import RequirementAnalyzer


class AutoLoopAgent:
    """自動ループエージェント"""

    def __init__(
        self,
        max_iterations: int = 5,
        output_dir: Optional[Path] = None,
    ):
        self.max_iterations = max_iterations
        self.output_dir = output_dir or OUTPUT_DIR

        # エージェント初期化
        self.validator = ArchitectureValidator()
        self.generator = CodeGenerator(output_dir=self.output_dir)
        self.issue_manager = IssueManager()
        self.requirement_analyzer = RequirementAnalyzer()

        # 実行ログ
        self.execution_log: List[Dict[str, Any]] = []
        LOG_DIR.mkdir(exist_ok=True)

    async def run(self, mode: str = "full") -> Dict[str, Any]:
        """
        自動ループを実行

        Args:
            mode: 実行モード
                - "full": 全て実行（検証 → 基盤生成 → Feature生成）
                - "validate": 検証のみ
                - "generate-core": 基盤コード生成のみ
                - "generate-features": Feature生成のみ
        """
        start_time = datetime.now()
        result = {
            "mode": mode,
            "start_time": start_time.isoformat(),
            "iterations": 0,
            "status": "running",
            "generated_files": [],
            "violations_fixed": 0,
            "remaining_violations": 0,
        }

        print(f"\n{'='*60}")
        print("浦和カップ SDK生成エージェント - 自動ループ開始")
        print(f"モード: {mode}")
        print(f"出力先: {self.output_dir}")
        print(f"{'='*60}\n")

        try:
            if mode == "validate":
                await self._run_validation_only(result)
            elif mode == "generate-core":
                await self._run_generate_core(result)
            elif mode == "generate-features":
                await self._run_generate_features(result)
            else:  # full
                await self._run_full_loop(result)

            result["status"] = "completed"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"\n❌ エラー発生: {e}")

        result["end_time"] = datetime.now().isoformat()
        result["duration_seconds"] = (datetime.now() - start_time).total_seconds()

        # ログ保存
        self._save_log(result)

        self._print_summary(result)

        return result

    async def _run_validation_only(self, result: Dict[str, Any]):
        """検証のみ実行"""
        print("📋 アーキテクチャ検証を実行中...")

        validation_result = self.validator.validate()
        result["validation"] = validation_result.to_dict()
        result["remaining_violations"] = len(validation_result.violations)

        print(self.validator.generate_report(validation_result))

    async def _run_generate_core(self, result: Dict[str, Any]):
        """基盤コード生成"""
        print("🔧 基盤コード（core/）を生成中...")

        core_files = self.generator.generate_core()
        written = self.generator.write_files(core_files)

        result["generated_files"].extend(written)
        print(f"\n✅ {len(written)}ファイルを生成しました")

    async def _run_generate_features(self, result: Dict[str, Any]):
        """Feature生成"""
        print("📦 Featureモジュールを生成中...")

        for feature_name in FEATURES:
            print(f"  - {feature_name}...")
            feature_files = self.generator.generate_feature(feature_name)
            written = self.generator.write_files(feature_files)
            result["generated_files"].extend(written)

        print(f"\n✅ {len(result['generated_files'])}ファイルを生成しました")

    async def _run_full_loop(self, result: Dict[str, Any]):
        """フルループ実行"""
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            result["iterations"] = iteration

            print(f"\n{'='*40}")
            print(f"イテレーション {iteration}/{self.max_iterations}")
            print(f"{'='*40}")

            # 1. アーキテクチャ検証
            print("\n📋 Step 1: アーキテクチャ検証")
            validation_result = self.validator.validate()

            if validation_result.status == "pass":
                print("✅ アーキテクチャ検証パス - ループ終了")
                result["validation"] = validation_result.to_dict()
                result["remaining_violations"] = 0
                break

            print(f"⚠️ {len(validation_result.violations)}件の違反を検出")

            # 2. Issue作成
            print("\n📝 Step 2: Issue作成")
            for violation in validation_result.violations:
                self.issue_manager.create_issue(
                    title=f"[{violation.rule_id}] {violation.rule}",
                    description=violation.description,
                    category="architecture",
                    severity=violation.severity,
                    location=violation.location,
                    fix_suggestion=violation.fix,
                )

            # 3. 基盤コード生成（初回のみ）
            if iteration == 1:
                print("\n🔧 Step 3: 基盤コード生成")
                core_files = self.generator.generate_core()
                written = self.generator.write_files(core_files)
                result["generated_files"].extend(written)
                print(f"  {len(written)}ファイルを生成")

            # 4. Feature生成（2回目以降）
            if iteration >= 2:
                print("\n📦 Step 4: Feature生成")
                for feature_name in FEATURES:
                    if not self._feature_exists(feature_name):
                        print(f"  - {feature_name}を生成中...")
                        feature_files = self.generator.generate_feature(feature_name)
                        written = self.generator.write_files(feature_files)
                        result["generated_files"].extend(written)

            result["violations_fixed"] += len(validation_result.violations)

            # 短い待機
            await asyncio.sleep(0.5)

        result["remaining_violations"] = len(
            self.validator.validate().violations
        )

    def _feature_exists(self, feature_name: str) -> bool:
        """Featureが既に存在するかチェック"""
        feature_path = self.output_dir / "features" / feature_name
        return feature_path.exists() and (feature_path / "index.ts").exists()

    def _save_log(self, result: Dict[str, Any]):
        """実行ログを保存"""
        log_file = LOG_DIR / f"autoloop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"\n📄 ログ保存: {log_file}")

    def _print_summary(self, result: Dict[str, Any]):
        """サマリーを出力"""
        print(f"\n{'='*60}")
        print("実行サマリー")
        print(f"{'='*60}")
        print(f"ステータス: {result['status']}")
        print(f"イテレーション: {result['iterations']}")
        print(f"生成ファイル数: {len(result['generated_files'])}")
        print(f"修正した違反: {result['violations_fixed']}")
        print(f"残りの違反: {result['remaining_violations']}")
        print(f"実行時間: {result.get('duration_seconds', 0):.2f}秒")
        print(f"{'='*60}")


async def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="浦和カップ SDK生成自動ループ")
    parser.add_argument(
        "mode",
        choices=["full", "validate", "generate-core", "generate-features"],
        default="full",
        nargs="?",
        help="実行モード",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="最大イテレーション数",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="出力ディレクトリ",
    )

    args = parser.parse_args()

    agent = AutoLoopAgent(
        max_iterations=args.max_iterations,
        output_dir=args.output,
    )

    await agent.run(mode=args.mode)


if __name__ == "__main__":
    asyncio.run(main())
