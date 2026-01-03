"""
浦和カップ SDK生成エージェント - 設定
SystemDesign_v2.mdに基づくアーキテクチャ

参照ドキュメント:
- SystemDesign_v2.md: システム設計
- SDK_CREATION_PROMPT.md: SDK生成プロンプト
- Issue/RootCauseAnalysis.md: 根本原因分析
"""

import os
from pathlib import Path
from typing import Dict, List, Any

# パス設定
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
OUTPUT_DIR = Path(os.getenv("URAWA_OUTPUT_DIR", BASE_DIR / "outputs"))
LOG_DIR = BASE_DIR / "logs"
ISSUE_DIR = PROJECT_ROOT / "Issue"
TEMPLATE_DIR = BASE_DIR / "templates"

# 入力ファイルパス
REQUIREMENT_SPEC_PATH = PROJECT_ROOT / "Requirement" / "RequirementSpecification.md"
SYSTEM_DESIGN_PATH = PROJECT_ROOT / "SystemDesign_v2.md"
ROOT_CAUSE_ANALYSIS_PATH = PROJECT_ROOT / "Issue" / "RootCauseAnalysis.md"
DATABASE_STRUCTURE_PATH = PROJECT_ROOT / "Issue" / "DatabaseStructure.md"
SDK_CREATION_PROMPT_PATH = PROJECT_ROOT / "SDK_CREATION_PROMPT.md"

# フロントエンドソースパス
FRONTEND_SRC_PATH = PROJECT_ROOT / "src" / "frontend" / "src"

# Anthropic API設定
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-sonnet-4-20250514"

# 生成対象Feature一覧
FEATURES = [
    "tournaments",
    "teams",
    "players",
    "matches",
    "standings",
    "exclusions",
    "reports",
    "venues",
]

# ============================================
# Core ディレクトリ構成（SystemDesign_v2.md準拠）
# ============================================
CORE_STRUCTURE = {
    "http": {
        "files": [
            "client.ts",           # シングルトンHTTPクライアント
            "index.ts",
        ],
        "interceptors": [
            "auth.ts",             # 認証ヘッダー付与
            "error.ts",            # エラー正規化（AppError形式）
            "transform.ts",        # snake_case ↔ camelCase自動変換
        ],
    },
    "auth": {
        "files": [
            "manager.ts",          # AuthManager（シングルトン）
            "store.ts",            # Zustand認証ストア
            "index.ts",
        ],
    },
    "errors": {
        "files": [
            "types.ts",            # AppError統一型
            "handler.ts",          # グローバルエラーハンドラ
            "index.ts",
        ],
    },
    "sync": {
        "files": [
            "queue.ts",            # SyncQueue
            "storage.ts",          # IndexedDB操作
            "conflict.ts",         # 競合解決
            "index.ts",
        ],
    },
    "config": {
        "files": [
            "index.ts",            # 環境設定
        ],
    },
}

# ============================================
# Feature モジュール構成
# ============================================
FEATURE_STRUCTURE = {
    "files": [
        "api.ts",          # API呼び出し（httpClient使用）
        "hooks.ts",        # React Query hooks
        "types.ts",        # 型定義
        "index.ts",        # 公開API
    ],
    "directories": [
        "components",      # UIコンポーネント
    ],
}

# Agent SDK 設定
AGENT_CONFIG = {
    # 使用するモデル（指定しない場合はデフォルト）
    "model": None,  # "sonnet", "opus", "haiku"

    # パーミッションモード
    "permission_mode": "acceptEdits",

    # システムプロンプト（追加指示）
    "system_prompt": """
あなたは浦和カップトーナメント管理システムのフロントエンドSDKを生成するエンジニアです。

## アーキテクチャ原則
1. HTTPクライアントは1つのみ（src/core/http/client.ts）
2. 認証はAuthManagerで一元管理
3. エラーはAppError形式に正規化
4. 命名規則はインターセプターで自動変換（snake_case ↔ camelCase）

## 技術スタック
- フロントエンド: React + TypeScript + Vite + Tailwind CSS
- 状態管理: Zustand + React Query
- HTTPクライアント: Axios（シングルトン）

## コーディング規約
- TypeScript: strictモード、型定義必須
- React: 関数コンポーネント + Hooks
- コメント: 日本語で記述
""",
}

# ============================================
# アーキテクチャ検証ルール（RootCauseAnalysis.md準拠）
# ============================================
ARCHITECTURE_RULES = {
    "single_http_client": {
        "id": "ARCH-001",
        "description": "HTTPクライアントは1つのみ（src/core/http/client.ts）",
        "severity": "critical",
        "forbidden_patterns": [
            "utils/api.ts",
            "utils/apiClient.ts",
            "api/client.ts",
        ],
        "allowed_patterns": [
            "core/http/client.ts",
        ],
        "fix": "全てのAPI呼び出しを core/http/client.ts 経由に統一",
    },
    "centralized_auth": {
        "id": "ARCH-002",
        "description": "認証はAuthManagerで一元管理",
        "severity": "critical",
        "required_files": [
            "core/auth/manager.ts",
            "core/auth/store.ts",
        ],
        "forbidden_patterns": [
            "localStorage.getItem.*token",  # 直接アクセス禁止
        ],
        "fix": "トークンは AuthManager 経由でのみアクセス",
    },
    "unified_error_format": {
        "id": "ARCH-003",
        "description": "エラーはAppError形式に正規化",
        "severity": "high",
        "required_files": [
            "core/errors/types.ts",
            "core/errors/handler.ts",
        ],
        "error_format": {
            "code": "ErrorCode",
            "message": "string",
            "status": "number",
            "details": "object",
            "retryable": "boolean",
        },
        "fix": "全エラーをエラーインターセプターでAppError形式に変換",
    },
    "auto_naming_conversion": {
        "id": "ARCH-004",
        "description": "命名規則はインターセプターで自動変換",
        "severity": "high",
        "required_files": [
            "core/http/interceptors/transform.ts",
        ],
        "rules": {
            "request": "camelCase → snake_case",
            "response": "snake_case → camelCase",
        },
        "fix": "変換インターセプターを必ず適用",
    },
    "offline_support": {
        "id": "ARCH-005",
        "description": "オフライン対応（SyncQueue）",
        "severity": "medium",
        "required_files": [
            "core/sync/queue.ts",
            "core/sync/storage.ts",
        ],
        "fix": "IndexedDBでオフラインキュー実装",
    },
}

# ============================================
# 削除対象ファイル（マイグレーション時）
# ============================================
DEPRECATED_FILES = [
    "utils/api.ts",
    "utils/apiClient.ts",
    "api/client.ts",
]

# ============================================
# エラーコード定義
# ============================================
ERROR_CODES = [
    "BAD_REQUEST",
    "UNAUTHORIZED",
    "FORBIDDEN",
    "NOT_FOUND",
    "CONFLICT",
    "VERSION_CONFLICT",
    "LOCK_CONFLICT",
    "VALIDATION_ERROR",
    "OFFLINE",
    "SYNC_ERROR",
    "SERVER_ERROR",
    "UNKNOWN",
]

# タスク優先度の定義
PRIORITY_ORDER = {
    "最高": 1,
    "高": 2,
    "中": 3,
    "低": 4
}

# 大会固定情報
TOURNAMENT_CONFIG = {
    "name": "さいたま市招待高校サッカーフェスティバル浦和カップ",
    "teams_count": 24,
    "groups": ["A", "B", "C", "D"],
    "teams_per_group": 6,
    "match_duration": 50,  # 分
    "half_duration": 25,   # 分
    "interval": 15,        # 分
    "matches_per_day": 6,  # 1会場あたり
    "days": 3,

    # 会場担当校（各グループの1番に固定）
    "venue_hosts": {
        "A": "浦和南",
        "B": "市立浦和",
        "C": "浦和学院",
        "D": "武南"
    },

    # 地元チーム
    "local_teams": [
        "浦和南", "市立浦和", "浦和学院", "武南",  # 会場担当校
        "県立浦和", "浦和西", "浦和東", "浦和レッズユース", "大宮アルディージャU18"
    ],

    # 報告書送信先
    "report_recipients": [
        "埼玉新聞",
        "テレビ埼玉",
        "イシクラ",
        "埼玉県サッカー協会"
    ]
}

# 順位決定ルール
STANDING_RULES = [
    "勝点（勝利=3点、引分=1点、敗北=0点）",
    "得失点差",
    "総得点",
    "当該チーム間の対戦成績",
    "抽選"
]
