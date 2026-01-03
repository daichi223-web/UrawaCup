"""
浦和カップ SDK生成エージェント

SystemDesign_v2.md に基づき、フロントエンドSDKを自動生成する
アーキテクチャ準拠のコード生成ツール

使用方法:
  python main.py generate-core              # 基盤コード生成（core/）
  python main.py generate-feature --name teams  # Feature Module生成
  python main.py validate-architecture      # アーキテクチャ検証
  python main.py autoloop                   # 自動ループ（検証→生成→再検証）
  python main.py migrate --from utils/api.ts --to core/http/client.ts  # マイグレーション
  python main.py list                       # タスク一覧表示
  python main.py run <task_id>              # 特定タスク実行（レガシー）
"""

import asyncio
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Windows環境でのUTF-8対応
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32':
    # コンソール出力のエンコーディングを設定
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass  # Python 3.7未満の場合は無視

# Agent SDK インポート
try:
    from claude_agent_sdk import query, ClaudeAgentOptions
    AGENT_SDK_AVAILABLE = True
except ImportError:
    AGENT_SDK_AVAILABLE = False
    print("警告: claude-agent-sdk がインストールされていません")
    print("インストール: python -m pip install claude-agent-sdk")

# プロジェクトのルートディレクトリ
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_REQUIREMENT_PATH = PROJECT_ROOT / "Requirement" / "requirement.md"
OUTPUT_DIR = PROJECT_ROOT / "src"
LOG_DIR = Path(__file__).parent / "logs"
ISSUE_DIR = PROJECT_ROOT / "Issue"


class TaskDefinition:
    """タスク定義"""

    TASKS = [
        {
            "id": "01_project_setup",
            "name": "プロジェクト初期設定",
            "priority": 1,
            "prompt": """
プロジェクトの初期設定を行ってください。

1. 以下のディレクトリ構造を作成:
   src/
   ├── backend/          # バックエンドAPI (FastAPI)
   │   ├── models/       # SQLAlchemyモデル
   │   ├── routes/       # APIルート
   │   ├── services/     # ビジネスロジック
   │   └── utils/        # ユーティリティ
   ├── frontend/         # フロントエンド (React + Vite)
   │   └── src/
   │       ├── components/
   │       ├── pages/
   │       ├── hooks/
   │       └── utils/
   └── shared/           # 共有型定義

2. frontend/package.json を作成（React + TypeScript + Vite + TailwindCSS）
3. backend/requirements.txt を作成（FastAPI + SQLAlchemy + その他）
4. 基本的な設定ファイルを作成
"""
        },
        {
            "id": "02_data_models",
            "name": "データモデル定義",
            "priority": 1,
            "prompt": """
データモデルを作成してください。

主要エンティティ:
- Tournament: 大会情報
- Team: チーム情報（地元/招待区分、会場担当フラグ）
- Player: 選手情報（背番号、選手名）
- Group: グループ情報（A〜D）
- Venue: 会場情報
- Match: 試合情報（スコア含む）
- Goal: 得点情報
- Standing: 順位情報（勝点、得失点差等）

作成物:
1. shared/types/index.ts - TypeScript型定義
2. backend/models/ - SQLAlchemy + Pydanticモデル
3. backend/database.py - DB接続設定
"""
        },
        {
            "id": "03_backend_api",
            "name": "バックエンドAPI構築",
            "priority": 1,
            "prompt": """
FastAPIでバックエンドAPIを構築してください。

エンドポイント:
1. /api/tournaments - 大会管理
2. /api/teams - チーム管理（CRUD + CSVインポート）
3. /api/players - 選手管理
4. /api/venues - 会場管理
5. /api/matches - 試合管理（日程生成、スコア入力）
6. /api/standings - 順位表
7. /api/reports - 報告書生成

作成物:
- backend/main.py - FastAPIアプリ
- backend/routes/*.py - 各エンドポイント
- backend/services/*.py - ビジネスロジック
"""
        },
        {
            "id": "04_frontend_base",
            "name": "フロントエンド基盤構築",
            "priority": 1,
            "prompt": """
React + TypeScript + Viteでフロントエンドを構築してください。

1. Viteプロジェクト初期化
2. TailwindCSS設定
3. React Router設定
4. レイアウトコンポーネント（Header, Sidebar, Layout）
5. API通信ユーティリティ
6. Zustand状態管理
"""
        },
        {
            "id": "05_team_management",
            "name": "チーム管理機能",
            "priority": 2,
            "prompt": """
チーム管理機能を実装してください。

機能:
1. チーム一覧（グループ別表示）
2. チーム登録・編集・削除
3. CSV一括インポート
4. グループ配置（会場担当校は固定: A1=浦和南, B1=市立浦和, C1=浦和学院, D1=武南）
"""
        },
        {
            "id": "06_match_input",
            "name": "試合結果入力機能",
            "priority": 1,
            "prompt": """
試合結果入力機能を実装してください。

入力項目:
- スコア（前半・後半・合計・PK）
- 得点時間、得点者名（サジェスト付き）

UI要件:
- 会場別試合一覧
- モバイルファースト（大きなタップ領域）
- オフライン対応（ローカルストレージ）
"""
        },
        {
            "id": "07_standings",
            "name": "順位表自動計算機能",
            "priority": 1,
            "prompt": """
順位表自動計算機能を実装してください。

順位決定ルール（優先順）:
1. 勝点（勝利=3, 引分=1, 敗北=0）
2. 得失点差
3. 総得点
4. 当該チーム間対戦成績
5. 抽選

リアルタイム更新、同勝点時の理由表示
"""
        },
        {
            "id": "08_schedule_generation",
            "name": "日程自動生成機能",
            "priority": 2,
            "prompt": """
予選リーグ日程の自動生成機能を実装してください。

要件:
- 6チーム変則リーグ（各チーム4試合、2チーム除外）
- 対戦除外設定UI
- 12試合/グループ自動生成
- 各会場6試合/日 × 2日間
- 試合間隔65分、開始9:30
"""
        },
        {
            "id": "09_tournament_bracket",
            "name": "決勝トーナメント組み合わせ",
            "priority": 2,
            "prompt": """
決勝トーナメント組み合わせ機能を実装してください。

1位リーグ: A1位 vs B1位, C1位 vs D1位
研修試合: 同順位同士、予選未対戦が条件
対戦履歴チェック、手動調整可能
"""
        },
        {
            "id": "10_report_generation",
            "name": "報告書生成機能",
            "priority": 1,
            "prompt": """
報告書生成機能を実装してください。

出力形式: PDF, Excel
内容: 大会名、日付、会場、スコア、得点経過
出力単位: 日別、会場別
1会場最大6試合を1ページに
"""
        },
        {
            "id": "11_dashboard",
            "name": "ダッシュボード",
            "priority": 2,
            "prompt": """
ダッシュボードを実装してください。

表示内容:
- 大会進行状況
- 完了試合数/総試合数
- クイックアクセス
- 最新試合結果
- アラート（未入力試合等）
"""
        },
        {
            "id": "12_offline_sync",
            "name": "オフライン対応・同期機能",
            "priority": 3,
            "prompt": """
オフライン対応と同期機能を実装してください。

- Service Worker
- IndexedDB
- 競合解決ロジック
- WebSocketリアルタイム同期
"""
        },
        # === Issue対応タスク ===
        {
            "id": "issue_007_finals_bracket",
            "name": "Issue #007: 決勝トーナメント自動生成",
            "priority": 2,
            "prompt": """
Issue #007: 決勝トーナメント組み合わせ自動生成を実装してください。

現状:
- 研修試合の自動生成は `generate-training` で実装済み
- 決勝トーナメント枠の自動埋め機能が未実装

実装内容:
1. `src/backend/routes/matches.py` に `generate-finals` エンドポイント追加
2. 組み合わせパターン: A1位 vs B1位, C1位 vs D1位
3. 準決勝・3位決定戦・決勝の試合レコード自動生成
4. フロントエンドに決勝トーナメント表示・編集UI追加

技術要件:
- standing_service.py の get_group_first_place を活用
- 手動での組み合わせ変更も可能に
"""
        },
        {
            "id": "issue_008_approval_flow",
            "name": "Issue #008: 結果承認フロー",
            "priority": 2,
            "prompt": """
Issue #008: 結果承認フローを実装してください。

現状:
- 試合結果は直接登録される
- 会場入力→本部承認のワークフローがない

実装内容:
1. `Match` モデルに以下を追加:
   - approval_status: pending/approved/rejected (Enum)
   - approved_by: User ID
   - approved_at: datetime
2. APIエンドポイント:
   - POST /matches/{id}/approve - 承認
   - POST /matches/{id}/reject - 却下（理由付き）
   - GET /matches/pending - 承認待ち一覧
3. フロントエンド:
   - 承認待ちバッジ表示
   - 承認/却下ボタン（管理者のみ）
   - 承認履歴表示
"""
        },
        {
            "id": "issue_009_auth_permissions",
            "name": "Issue #009: 権限分離実装",
            "priority": 2,
            "prompt": """
Issue #009: 権限分離を完全実装してください。

現状:
- User モデルは存在する
- JWT認証の仕組みがない
- ルートに認証・認可がない

実装内容:
1. JWT認証ミドルウェア:
   - `src/backend/utils/auth.py` 作成
   - access_token, refresh_token 発行
2. 認可デコレータ:
   - get_current_user依存性
   - require_admin デコレータ
   - require_venue_manager デコレータ
3. ルート保護:
   - 編集系API: 認証必須
   - 閲覧API: 認証不要
   - 会場担当者: 自会場のみ編集可能
4. フロントエンド:
   - ログイン画面
   - トークン管理（localStorage）
   - 認証状態によるUI切り替え
"""
        },
        {
            "id": "issue_010_pwa",
            "name": "Issue #010: PWA/オフライン対応",
            "priority": 3,
            "prompt": """
Issue #010: PWA/オフライン対応を実装してください。

現状:
- 通常のSPAとして動作
- オフライン時は使用不可

実装内容:
1. `public/manifest.json` 作成:
   - アプリ名、アイコン、テーマカラー
   - display: standalone
2. Service Worker (`sw.js`):
   - 静的アセットのキャッシュ
   - APIレスポンスのキャッシュ戦略
   - オフライン時のフォールバック
3. IndexedDB:
   - Dexie.js 導入
   - 試合データのローカル保存
   - オフライン時の入力保持
4. 同期機能:
   - オンライン復帰時の自動同期
   - 競合検出・解決UI
5. Vite PWA プラグイン設定
"""
        },
        {
            "id": "issue_011_realtime",
            "name": "Issue #011: リアルタイム更新",
            "priority": 3,
            "prompt": """
Issue #011: リアルタイム更新機能を実装してください。

現状:
- ポーリングでの更新のみ
- 他ユーザーの変更が即座に反映されない

実装内容:
1. バックエンド WebSocket:
   - `src/backend/routes/websocket.py` 作成
   - FastAPI WebSocket エンドポイント
   - 接続管理（ConnectionManager クラス）
   - イベント: match_updated, standing_updated
2. フロントエンド:
   - WebSocket接続フック
   - 自動再接続ロジック
   - リアルタイム更新のトースト通知
3. ブロードキャスト:
   - 試合結果入力時に全クライアントへ通知
   - 順位表更新時に通知
"""
        },
        {
            "id": "issue_012_public_view",
            "name": "Issue #012: パブリックビュー",
            "priority": 2,
            "prompt": """
Issue #012: パブリックビューページを実装してください。

現状:
- 全ページが管理画面として設計
- ログイン不要の閲覧ページがない

実装内容:
1. 認証不要ルート（バックエンド）:
   - GET /api/public/standings - 順位表
   - GET /api/public/matches - 試合結果
   - GET /api/public/schedule - 日程
2. フロントエンドページ:
   - `/public/` プレフィックスのルート
   - `/public/standings` - 順位表閲覧
   - `/public/matches` - 試合結果一覧
   - `/public/schedule` - 日程表
3. UI要件:
   - シンプルで見やすいデザイン
   - リアルタイム更新対応
   - QRコード表示（会場掲示用）
   - 自動リフレッシュ（30秒ごと）
"""
        },
        # === 新規 Issue対応タスク (2026-01-01追加) ===
        {
            "id": "issue_009a_secret_key",
            "name": "Issue #009-A: SECRET_KEY設定",
            "priority": 1,
            "prompt": """
Issue #009-A: SECRET_KEYのセキュリティ問題を解決してください。

現状:
- `src/backend/config.py` で `secret_key: str = "your-secret-key-change-in-production"` とデフォルト値
- 本番環境でセキュリティリスク

実装内容:
1. `src/backend/.env.example` を作成:
   ```
   SECRET_KEY=your-random-secret-key-here
   DATABASE_URL=sqlite:///./urawacup.db
   ```
2. `config.py` を修正して起動時にSECRET_KEYのデフォルト値警告を出す
3. `python-dotenv` で .env ファイル読み込み対応
"""
        },
        {
            "id": "issue_009b_camelcase",
            "name": "Issue #009-B: camelCase対応",
            "priority": 2,
            "prompt": """
Issue #009-B: snake_case/camelCase不一致を解決してください。

現状:
- バックエンド: `access_token` (snake_case)
- フロントエンド: `accessToken` (camelCase) を期待

実装内容:
1. `src/backend/schemas/common.py` に CamelCaseModel ベースクラスを追加:
   ```python
   from pydantic import BaseModel, ConfigDict
   from pydantic.alias_generators import to_camel

   class CamelCaseModel(BaseModel):
       model_config = ConfigDict(
           alias_generator=to_camel,
           populate_by_name=True,
           from_attributes=True,
       )
   ```
2. `src/backend/schemas/user.py` の TokenResponse を CamelCaseModel から継承
3. フロントエンドとの互換性を確認
"""
        },
        {
            "id": "issue_009c_admin_script",
            "name": "Issue #009-C: 管理者作成スクリプト",
            "priority": 1,
            "prompt": """
Issue #009-C: 初期管理者ユーザー作成スクリプトを実装してください。

現状:
- 管理者を作成する手段がない
- APIからはパスワードハッシュを直接設定できない

実装内容:
1. `src/backend/scripts/create_admin.py` を作成:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

   from database import SessionLocal
   from models.user import User, UserRole
   from utils.auth import hash_password

   def create_admin(username: str, password: str, display_name: str):
       db = SessionLocal()
       try:
           existing = db.query(User).filter(User.username == username).first()
           if existing:
               print(f"ユーザー '{username}' は既に存在します")
               return

           admin = User(
               username=username,
               password_hash=hash_password(password),
               display_name=display_name,
               role=UserRole.ADMIN,
               is_active=True,
           )
           db.add(admin)
           db.commit()
           print(f"管理者 '{username}' を作成しました")
       finally:
           db.close()

   if __name__ == "__main__":
       if len(sys.argv) >= 4:
           create_admin(sys.argv[1], sys.argv[2], sys.argv[3])
       else:
           create_admin("admin", "admin1234", "システム管理者")
   ```
2. 実行方法を README に追記
"""
        },
        {
            "id": "issue_016_scorer_ranking_ui",
            "name": "Issue #016: 得点ランキングUI",
            "priority": 2,
            "prompt": """
Issue #016: 得点ランキング画面をフロントエンドに追加してください。

現状:
- バックエンドAPI `/api/standings/top-scorers` は実装済み
- フロントエンドに表示UIがない

実装内容:
1. `src/frontend/src/api/standings.ts` に `getTopScorers` 関数を追加:
   ```typescript
   export const standingApi = {
     // 既存のメソッド...
     getTopScorers: async (tournamentId: number, limit: number = 10) => {
       const response = await apiClient.get(`/standings/top-scorers`, {
         params: { tournament_id: tournamentId, limit }
       });
       return response.data;
     }
   };
   ```

2. `src/frontend/src/pages/ScorerRanking.tsx` を作成:
   - 得点ランキング一覧表示
   - 順位、選手名、所属チーム、得点数を表示
   - 金銀銅メダルアイコン（1〜3位）
   - 現在の大会の得点ランキングを表示

3. `src/frontend/src/App.tsx` にルート追加:
   ```tsx
   <Route path="/scorer-ranking" element={<ScorerRanking />} />
   ```

4. サイドバー/ナビゲーションにリンク追加

デザイン要件:
- Tailwind CSSを使用
- 他のページと統一感のあるデザイン
- レスポンシブ対応
"""
        }
    ]


class UrawaCupAgentBuilder:
    """浦和カップシステム自動構築エージェント"""

    def __init__(self, requirement_path: Path = None, project_path: Path = None):
        self.requirement_path = requirement_path or DEFAULT_REQUIREMENT_PATH
        self.project_path = project_path or OUTPUT_DIR
        self.tasks = TaskDefinition.TASKS
        self.completed_tasks = []
        self.failed_tasks = []
        self.issues = []

        # ログディレクトリ作成
        LOG_DIR.mkdir(exist_ok=True)
        ISSUE_DIR.mkdir(exist_ok=True)

    def _load_requirement(self) -> str:
        """要件定義書を読み込み"""
        if self.requirement_path.exists():
            return self.requirement_path.read_text(encoding="utf-8")
        return ""

    def _build_prompt(self, task: dict) -> str:
        """タスク用プロンプトを構築"""
        requirement = self._load_requirement()

        return f"""
あなたは浦和カップトーナメント管理システムを構築するエンジニアです。

## 要件定義書
{requirement}

## 現在のタスク: {task['name']}
{task['prompt']}

## 作業ディレクトリ
{self.project_path}

## 注意事項
- 既存コードがあれば活かして実装
- TypeScript/Reactのベストプラクティスに従う
- バックエンドはPython FastAPI
- 適切なエラーハンドリング
- 日本語コメント推奨

実装を開始してください。
"""

    async def run_task(self, task: dict) -> dict:
        """個別タスクの実行"""
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] タスク実行: {task['name']}")
        print(f"ID: {task['id']} | 優先度: {task['priority']}")
        print(f"{'='*60}\n")

        result = {
            "task_id": task["id"],
            "task_name": task["name"],
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "output": [],
            "errors": []
        }

        if not AGENT_SDK_AVAILABLE:
            result["status"] = "error"
            result["errors"].append("claude-agent-sdk not installed")
            return result

        try:
            prompt = self._build_prompt(task)

            options = ClaudeAgentOptions(
                allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
                permission_mode="bypassPermissions",
                cwd=str(PROJECT_ROOT)
            )

            # クエリ実行
            query_gen = query(prompt=prompt, options=options)

            try:
                async for message in query_gen:
                    msg_type = type(message).__name__

                    # SystemMessageの処理
                    if msg_type == 'SystemMessage':
                        if hasattr(message, 'subtype') and message.subtype == 'init':
                            print(f"[Session: {getattr(message.data, 'session_id', 'N/A')[:8]}...]")

                    # AssistantMessageの処理
                    elif msg_type == 'AssistantMessage':
                        if hasattr(message, 'content'):
                            for block in message.content:
                                if hasattr(block, 'text'):
                                    text = str(block.text)
                                    print(text)
                                    result["output"].append(text)
                                elif hasattr(block, 'name'):
                                    print(f"[Tool: {block.name}]")

                    # ResultMessageの処理
                    elif msg_type == 'ResultMessage':
                        result["status"] = "completed"
                        print("\n[タスク完了]")

            finally:
                # ジェネレータを適切にクローズ
                await query_gen.aclose()

        except GeneratorExit:
            result["status"] = "completed"
        except Exception as e:
            result["status"] = "error"
            error_msg = str(e)
            result["errors"].append(error_msg)
            print(f"エラー発生: {error_msg}")
            self._add_issue(task, error_msg)

        result["end_time"] = datetime.now().isoformat()
        self._save_log(task["id"], result)

        return result

    def _save_log(self, task_id: str, result: dict):
        """ログを保存"""
        log_file = LOG_DIR / f"{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    def _add_issue(self, task: dict, error: str):
        """Issueを追加"""
        issue = {
            "id": len(self.issues) + 1,
            "task_id": task["id"],
            "task_name": task["name"],
            "error": error,
            "created_at": datetime.now().isoformat(),
            "status": "open"
        }
        self.issues.append(issue)
        self._save_issues()

    def _save_issues(self):
        """Issue一覧を保存"""
        issue_file = ISSUE_DIR / "Issue.md"

        content = "# 浦和カップ トーナメント管理システム - Issue一覧\n\n"
        content += f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        open_issues = [i for i in self.issues if i["status"] == "open"]
        closed_issues = [i for i in self.issues if i["status"] == "closed"]

        content += f"## Open Issues ({len(open_issues)})\n\n"
        for issue in open_issues:
            content += f"### Issue #{issue['id']:03d}: {issue['task_name']}\n"
            content += f"- **タスクID**: {issue['task_id']}\n"
            content += f"- **エラー**: {issue['error']}\n"
            content += f"- **作成日時**: {issue['created_at']}\n\n"

        content += f"\n## Closed Issues ({len(closed_issues)})\n\n"
        for issue in closed_issues:
            content += f"- ~~Issue #{issue['id']:03d}: {issue['task_name']}~~\n"

        issue_file.write_text(content, encoding="utf-8")

    async def autoloop(self, max_retries: int = 3):
        """全タスクを自動ループ実行"""
        print("\n" + "="*60)
        print("浦和カップ トーナメント管理システム - 自動構築開始")
        print(f"要件定義書: {self.requirement_path}")
        print(f"出力先: {self.project_path}")
        print("="*60 + "\n")

        # 優先度順にソート
        sorted_tasks = sorted(self.tasks, key=lambda x: x["priority"])

        for task in sorted_tasks:
            if task["id"] in self.completed_tasks:
                print(f"[スキップ] {task['name']} (完了済み)")
                continue

            retries = 0
            while retries < max_retries:
                result = await self.run_task(task)

                if result["status"] == "completed":
                    self.completed_tasks.append(task["id"])
                    print(f"\n✓ {task['name']} 完了\n")
                    break
                else:
                    retries += 1
                    if retries < max_retries:
                        print(f"\n再試行 ({retries}/{max_retries})...\n")
                        await asyncio.sleep(2)
                    else:
                        self.failed_tasks.append(task["id"])
                        print(f"\n✗ {task['name']} 失敗（最大リトライ回数超過）\n")

        # 最終レポート
        self._print_final_report()

    def _print_final_report(self):
        """最終レポート出力"""
        print("\n" + "="*60)
        print("構築完了レポート")
        print("="*60)
        print(f"完了: {len(self.completed_tasks)}/{len(self.tasks)}")
        print(f"失敗: {len(self.failed_tasks)}")
        print(f"Issue: {len(self.issues)}")
        print("-"*60)

        for task in self.tasks:
            if task["id"] in self.completed_tasks:
                print(f"  ✓ {task['name']}")
            elif task["id"] in self.failed_tasks:
                print(f"  ✗ {task['name']}")
            else:
                print(f"  - {task['name']}")

    def list_tasks(self):
        """タスク一覧を表示"""
        print("\n利用可能なタスク:")
        print("-" * 60)
        for task in sorted(self.tasks, key=lambda x: x["priority"]):
            status = "✓" if task["id"] in self.completed_tasks else " "
            print(f"  [{status}] {task['id']}: {task['name']} (P{task['priority']})")
        print("-" * 60)


def parse_args():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description="浦和カップ SDK生成エージェント"
    )

    subparsers = parser.add_subparsers(dest="command", help="コマンド")

    # generate-core コマンド
    core_parser = subparsers.add_parser("generate-core", help="基盤コード生成（core/）")
    core_parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="出力ディレクトリ"
    )

    # generate-feature コマンド
    feature_parser = subparsers.add_parser("generate-feature", help="Feature Module生成")
    feature_parser.add_argument(
        "--name",
        required=True,
        help="Feature名（teams, matches, standings等）"
    )
    feature_parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="出力ディレクトリ"
    )

    # validate-architecture コマンド
    validate_parser = subparsers.add_parser("validate-architecture", help="アーキテクチャ検証")
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="JSON形式で出力"
    )
    validate_parser.add_argument(
        "--create-issues",
        action="store_true",
        help="違反からIssueを作成"
    )

    # autoloop コマンド
    autoloop_parser = subparsers.add_parser("autoloop", help="自動ループ実行")
    autoloop_parser.add_argument(
        "-r", "--requirement",
        type=Path,
        default=DEFAULT_REQUIREMENT_PATH,
        help="要件定義書のパス"
    )
    autoloop_parser.add_argument(
        "-p", "--project",
        type=Path,
        default=OUTPUT_DIR,
        help="出力先プロジェクトパス"
    )
    autoloop_parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="最大リトライ回数"
    )
    autoloop_parser.add_argument(
        "--mode",
        choices=["full", "validate", "generate-core", "generate-features"],
        default="full",
        help="実行モード"
    )

    # migrate コマンド
    migrate_parser = subparsers.add_parser("migrate", help="コードマイグレーション")
    migrate_parser.add_argument(
        "--from",
        dest="from_file",
        required=True,
        help="移行元ファイル"
    )
    migrate_parser.add_argument(
        "--to",
        dest="to_file",
        required=True,
        help="移行先ファイル"
    )

    # list コマンド
    subparsers.add_parser("list", help="タスク一覧表示")

    # run コマンド（レガシー）
    run_parser = subparsers.add_parser("run", help="特定タスク実行（レガシー）")
    run_parser.add_argument("task_id", help="タスクID")

    return parser.parse_args()


async def main():
    """メイン実行関数"""
    args = parse_args()

    # 新しいエージェントをインポート
    try:
        from agents import CodeGenerator, ArchitectureValidator, AutoLoopAgent
        NEW_AGENTS_AVAILABLE = True
    except ImportError:
        NEW_AGENTS_AVAILABLE = False

    if args.command == "generate-core":
        if not NEW_AGENTS_AVAILABLE:
            print("エラー: agentsモジュールがインポートできません")
            return
        generator = CodeGenerator(output_dir=args.output)
        files = generator.generate_core()
        generator.write_files(files)
        print(f"\n✅ {len(files)}ファイルを生成しました")

    elif args.command == "generate-feature":
        if not NEW_AGENTS_AVAILABLE:
            print("エラー: agentsモジュールがインポートできません")
            return
        generator = CodeGenerator(output_dir=args.output)
        try:
            files = generator.generate_feature(args.name)
            generator.write_files(files)
            print(f"\n✅ Feature '{args.name}' を生成しました（{len(files)}ファイル）")
        except ValueError as e:
            print(f"エラー: {e}")

    elif args.command == "validate-architecture":
        if not NEW_AGENTS_AVAILABLE:
            print("エラー: agentsモジュールがインポートできません")
            return
        validator = ArchitectureValidator()
        result = validator.validate()

        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(validator.generate_report(result))

        if args.create_issues and result.violations:
            from agents import IssueManager
            issue_manager = IssueManager()
            for v in result.violations:
                issue_manager.create_issue(
                    title=f"[{v.rule_id}] {v.rule}",
                    description=v.description,
                    category="architecture",
                    severity=v.severity,
                    location=v.location,
                    fix_suggestion=v.fix,
                )
            print(f"\n📝 {len(result.violations)}件のIssueを作成しました")

    elif args.command == "migrate":
        print(f"マイグレーション: {args.from_file} → {args.to_file}")
        print("（この機能は将来実装予定です）")

    elif args.command == "autoloop":
        if NEW_AGENTS_AVAILABLE and hasattr(args, 'mode'):
            agent = AutoLoopAgent(
                max_iterations=args.retries,
                output_dir=args.project,
            )
            await agent.run(mode=args.mode)
        else:
            # レガシーモード
            builder = UrawaCupAgentBuilder(
                requirement_path=args.requirement,
                project_path=args.project
            )
            await builder.autoloop(max_retries=args.retries)

    elif args.command == "list":
        builder = UrawaCupAgentBuilder()
        builder.list_tasks()

    elif args.command == "run":
        builder = UrawaCupAgentBuilder()
        task = next((t for t in builder.tasks if t["id"] == args.task_id), None)
        if task:
            await builder.run_task(task)
        else:
            print(f"タスク '{args.task_id}' が見つかりません")
            builder.list_tasks()
    else:
        print("使用方法:")
        print("  python main.py generate-core              # 基盤コード生成")
        print("  python main.py generate-feature --name teams  # Feature生成")
        print("  python main.py validate-architecture      # アーキテクチャ検証")
        print("  python main.py autoloop                   # 自動ループ実行")
        print("  python main.py autoloop --mode validate   # 検証のみ")
        print("  python main.py migrate --from X --to Y    # マイグレーション")
        print("  python main.py list                       # タスク一覧")
        print("  python main.py run <task_id>              # 特定タスク実行")


if __name__ == "__main__":
    asyncio.run(main())
