"""
浦和カップ SDK生成エージェント - エージェントモジュール

SystemDesign_v2.md および SDK_CREATION_PROMPT.md に基づく
アーキテクチャ準拠のコード生成を行う。

重要な原則:
- 推測でコードを書かない
- 不明な点はIssueを作成して調査してからコーディングする
"""

from .issue_manager import IssueManager
from .requirement_analyzer import RequirementAnalyzer
from .code_generator import CodeGenerator
from .architecture_validator import ArchitectureValidator
from .auto_loop_agent import AutoLoopAgent
from .uncertainty_guard import UncertaintyGuard, uncertainty_guard

__all__ = [
    # Issue管理
    "IssueManager",

    # 要件分析
    "RequirementAnalyzer",

    # コード生成
    "CodeGenerator",

    # アーキテクチャ検証
    "ArchitectureValidator",

    # 自動ループ実行
    "AutoLoopAgent",

    # 不確実性ガード（推測防止）
    "UncertaintyGuard",
    "uncertainty_guard",
]
