# 浦和カップ SDK生成エージェント

SystemDesign_v2.md および SDK_CREATION_PROMPT.md に基づいて、アーキテクチャ準拠のフロントエンドコードを生成・検証するツールです。

## アーキテクチャ原則

このSDKは以下の原則に従ってコードを生成します：

### 1. 単一HTTPクライアント (ARCH-001)
- **場所**: `src/core/http/client.ts`
- 全てのAPI呼び出しはこのクライアント経由
- 禁止: `utils/api.ts`, `utils/apiClient.ts` 等の個別実装

### 2. 認証一元管理 (ARCH-002)
- **場所**: `src/core/auth/manager.ts`
- AuthManagerシングルトンでトークン管理
- 禁止: localStorageへの直接アクセス

### 3. エラー統一 (ARCH-003)
- **形式**: AppError型
- FastAPIの`{ detail: "..." }`形式に対応
- エラーコード: BAD_REQUEST, UNAUTHORIZED, FORBIDDEN, NOT_FOUND, etc.

### 4. 命名規則自動変換 (ARCH-004)
- フロントエンド: camelCase
- バックエンド: snake_case
- transformInterceptorで自動変換

## セットアップ

```bash
# Windows
setup.bat

# または手動で
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## コマンド

### コード生成

```bash
# Coreモジュール生成（HTTP, Auth, Error）
python main.py generate-core

# Feature生成
python main.py generate-feature --name teams
python main.py generate-feature --name matches
python main.py generate-feature --name standings
```

### アーキテクチャ検証

```bash
# 全検証実行
python main.py validate-architecture

# 出力例:
# ステータス: PASS | WARNING | FAIL
# 違反一覧（Critical/High/Medium）
```

### マイグレーション

```bash
# 非推奨ファイルからの移行分析
python main.py migrate --from utils/api.ts --to core/http/client.ts
```

### 自動ループ実行

```bash
# 全タスク自動実行
python main.py autoloop

# 特定タスクから実行
python main.py autoloop --start 05_team_management
```

### その他

```bash
# タスク一覧表示
python main.py list

# 指定タスク実行
python main.py run 01_project_setup
```

## ディレクトリ構造

### エージェント構成

```
agent-UrawaCup/
├── main.py                 # CLIエントリーポイント
├── config.py               # 設定・アーキテクチャルール
├── agents/
│   ├── __init__.py
│   ├── issue_manager.py         # Issue管理
│   ├── requirement_analyzer.py  # 要件解析
│   ├── code_generator.py        # コード生成
│   ├── architecture_validator.py # アーキテクチャ検証
│   └── auto_loop_agent.py       # 自動ループ実行
└── prompts/
    └── sdk_generation.md        # 生成プロンプト
```

### 生成されるCore構造

```
src/frontend/src/core/
├── http/
│   ├── client.ts           # 唯一のHTTPクライアント
│   ├── types.ts            # リクエスト/レスポンス型
│   └── interceptors/
│       ├── auth.ts         # 認証ヘッダー付与
│       ├── transform.ts    # snake_case ↔ camelCase
│       └── error.ts        # エラー変換
├── auth/
│   ├── manager.ts          # AuthManagerシングルトン
│   ├── types.ts            # 認証関連型
│   └── storage.ts          # トークン永続化
├── errors/
│   ├── types.ts            # AppError型
│   ├── codes.ts            # エラーコード定義
│   └── handler.ts          # エラーハンドリング
└── index.ts                # 統一エクスポート
```

### 生成されるFeature構造

```
src/frontend/src/features/{feature_name}/
├── api.ts                  # API呼び出し（httpClient使用）
├── hooks.ts                # React Query フック
├── types.ts                # Feature固有型
├── components/             # UIコンポーネント
└── index.ts                # 公開API
```

## 検証ルール

| ルールID | 名称 | 重要度 | 説明 |
|----------|------|--------|------|
| ARCH-001 | single_http_client | Critical | HTTPクライアントは1つのみ |
| ARCH-002 | centralized_auth | Critical | 認証はAuthManager経由 |
| ARCH-003 | unified_error | High | エラーはAppError形式 |
| ARCH-004 | naming_convention | High | 命名規則の自動変換 |
| ARCH-005 | feature_structure | Medium | Feature構造の統一 |

## Feature一覧

| Feature | 説明 | 優先度 |
|---------|------|--------|
| tournaments | 大会管理 | 1 |
| teams | チーム管理 | 1 |
| matches | 試合管理・結果入力 | 1 |
| standings | 順位表自動計算 | 1 |
| players | 選手管理 | 2 |
| exclusions | 対戦除外設定 | 2 |
| venues | 会場管理 | 2 |
| reports | 報告書生成 | 2 |

## 技術スタック

- **フロントエンド**: React + TypeScript + Vite + Tailwind CSS
- **バックエンド**: Python FastAPI + SQLAlchemy + SQLite
- **状態管理**: Zustand
- **データフェッチ**: TanStack Query (React Query)
- **PDF生成**: reportlab
- **Excel生成**: openpyxl

## 参照ドキュメント

- `D:\UrawaCup\SystemDesign_v2.md` - システム設計書
- `D:\UrawaCup\SDK_CREATION_PROMPT.md` - SDK生成プロンプト
- `D:\UrawaCup\Requirement\RequirementSpec.md` - 要件定義書
