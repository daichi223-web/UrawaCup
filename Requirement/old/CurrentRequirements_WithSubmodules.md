# 浦和カップ トーナメント管理システム
## 現在の要件定義書（サブモジュール含む）

**バージョン**: 2.1
**作成日**: 2026-01-03
**最終更新**: 2026-01-03

---

# 目次

1. [システム概要](#1-システム概要)
2. [機能要件一覧](#2-機能要件一覧)
3. [サブモジュール構成](#3-サブモジュール構成)
4. [画面一覧](#4-画面一覧)
5. [API一覧](#5-api一覧)
6. [データモデル](#6-データモデル)
7. [実装状況](#7-実装状況)

---

# 1. システム概要

## 1.1 システム構成

```
浦和カップ トーナメント管理システム
├── src/
│   ├── backend/          # FastAPI バックエンド
│   └── frontend/         # React フロントエンド
├── agent-UrawaCup/       # AI自動生成エージェント
├── requirement-checker-sdk/  # 要件チェッカーSDK
└── Requirement/          # 要件定義書
```

## 1.2 技術スタック

| レイヤー | 技術 | バージョン |
|----------|------|------------|
| フロントエンド | React + TypeScript + Vite | 18.x / 5.x |
| スタイリング | TailwindCSS | 3.x |
| 状態管理 | Zustand + TanStack Query | 4.x / 5.x |
| バックエンド | FastAPI + SQLAlchemy | 0.100+ / 2.x |
| データベース | SQLite | 3.x |
| PDF生成 | ReportLab | - |
| テスト | pytest + Playwright | - |

---

# 2. 機能要件一覧

## 2.1 大会管理機能

| ID | 機能 | 優先度 | ステータス |
|----|------|--------|------------|
| F-01 | 大会作成・編集 | 高 | ✅ 実装済 |
| F-02 | 大会設定（試合時間、インターバル等） | 高 | ✅ 実装済 |
| F-03 | グループ自動作成（A,B,C,D） | 高 | ✅ 実装済 |

## 2.2 チーム管理機能

| ID | 機能 | 優先度 | ステータス |
|----|------|--------|------------|
| F-10 | チーム登録・編集・削除 | 高 | ✅ 実装済 |
| F-11 | グループ割当 | 高 | ✅ 実装済 |
| F-12 | CSVインポート | 中 | ✅ 実装済 |
| F-13 | チーム区分設定（地元/招待） | 高 | ✅ 実装済 |
| F-14 | 会場担当校フラグ設定 | 高 | ✅ 実装済 |

## 2.3 選手管理機能

| ID | 機能 | 優先度 | ステータス |
|----|------|--------|------------|
| F-20 | 選手登録・編集・削除 | 高 | ✅ 実装済 |
| F-21 | Excel/CSVインポート | 高 | ✅ 実装済 |
| F-22 | 参加申込書形式インポート | 中 | ⚠️ 一部実装 |
| F-23 | 得点者サジェスト | 高 | ✅ 実装済 |
| F-24 | 選手検索 | 中 | ✅ 実装済 |

## 2.4 スタッフ管理機能

| ID | 機能 | 優先度 | ステータス |
|----|------|--------|------------|
| F-30 | スタッフ登録・編集・削除 | 高 | ✅ 実装済 |
| F-31 | 役割設定（監督/コーチ/帯同審判） | 高 | ✅ 実装済 |

## 2.5 会場管理機能

| ID | 機能 | 優先度 | ステータス |
|----|------|--------|------------|
| F-40 | 会場登録・編集・削除 | 高 | ✅ 実装済 |
| F-41 | グループ紐付け | 高 | ✅ 実装済 |
| F-42 | 試合数上限設定 | 中 | ✅ 実装済 |

## 2.6 日程管理機能

| ID | 機能 | 優先度 | ステータス |
|----|------|--------|------------|
| F-50 | 対戦除外設定 | 高 | ✅ 実装済 |
| F-51 | 予選日程自動生成 | 高 | ✅ 実装済 |
| F-52 | 決勝トーナメント生成 | 高 | ✅ 実装済 |
| F-53 | 研修試合生成 | 中 | ✅ 実装済 |
| F-54 | 日程手動調整 | 中 | ✅ 実装済 |
| F-55 | ドラッグ&ドロップ組み合わせ変更 | 中 | ✅ 実装済 |

## 2.7 試合結果入力機能

| ID | 機能 | 優先度 | ステータス |
|----|------|--------|------------|
| F-60 | スコア入力（前半/後半/合計） | 最高 | ✅ 実装済 |
| F-61 | PK戦スコア入力 | 高 | ✅ 実装済 |
| F-62 | 得点者入力（サジェスト付き） | 中 | ✅ 実装済 |
| F-63 | 入力ロック機能 | 高 | ✅ 実装済 |
| F-64 | 結果承認フロー | 中 | ✅ 実装済 |

## 2.8 順位表・統計機能

| ID | 機能 | 優先度 | ステータス |
|----|------|--------|------------|
| F-70 | 順位表自動計算 | 最高 | ✅ 実装済 |
| F-71 | グループ別順位表表示 | 高 | ✅ 実装済 |
| F-72 | 得点ランキング | 中 | ✅ 実装済 |
| F-73 | 統計ダッシュボード | 低 | ✅ 実装済 |

## 2.9 レポート出力機能

| ID | 機能 | 優先度 | ステータス |
|----|------|--------|------------|
| F-80 | 日次報告書PDF | 最高 | ✅ 実装済 |
| F-81 | グループ順位表PDF | 高 | ✅ 実装済 |
| F-82 | 最終日組み合わせ表PDF | 高 | ✅ 実装済 |
| F-83 | 最終結果報告書PDF | 高 | ✅ 実装済 |
| F-84 | Excel出力 | 中 | ✅ 実装済 |

## 2.10 公開機能

| ID | 機能 | 優先度 | ステータス |
|----|------|--------|------------|
| F-90 | 公開順位表 | 高 | ✅ 実装済 |
| F-91 | 公開試合一覧 | 高 | ✅ 実装済 |
| F-92 | WebSocketリアルタイム更新 | 中 | ✅ 実装済 |

## 2.11 オフライン・PWA機能

| ID | 機能 | 優先度 | ステータス |
|----|------|--------|------------|
| F-100 | オフライン入力対応 | 中 | ✅ 実装済 |
| F-101 | IndexedDBローカル保存 | 中 | ✅ 実装済 |
| F-102 | 競合解決UI | 中 | ✅ 実装済 |
| F-103 | オンライン復帰時同期 | 中 | ✅ 実装済 |

---

# 3. サブモジュール構成

## 3.1 バックエンド サブモジュール

### models/ - データモデル（16ファイル）

| ファイル | 説明 | 依存関係 |
|----------|------|----------|
| base.py | 共通基底クラス（TimestampMixin） | - |
| tournament.py | 大会情報 | base |
| group.py | グループ（A〜D） | tournament |
| team.py | チーム情報 | tournament, group |
| player.py | 選手情報 | team |
| staff.py | スタッフ情報 | team |
| team_uniform.py | ユニフォーム | team |
| venue.py | 会場情報 | tournament |
| match.py | 試合情報 | tournament, team, venue, group |
| goal.py | 得点記録 | match, team, player |
| standing.py | 順位表 | tournament, team, group |
| exclusion_pair.py | 対戦除外ペア | tournament, team |
| tournament_award.py | 表彰情報 | tournament, player |
| report_recipient.py | 報告書送信先 | tournament |
| user.py | ユーザー認証 | venue |

### routes/ - APIルート（11ファイル）

| ファイル | パス | 機能 |
|----------|------|------|
| auth.py | /api/auth/* | 認証・ログイン |
| tournaments.py | /api/tournaments/* | 大会CRUD |
| teams.py | /api/teams/* | チームCRUD、CSV |
| players.py | /api/players/* | 選手CRUD、サジェスト |
| staff.py | /api/staff/* | スタッフCRUD |
| venues.py | /api/venues/* | 会場CRUD |
| matches.py | /api/matches/* | 試合、日程生成、ロック |
| standings.py | /api/standings/* | 順位表、得点ランキング |
| exclusions.py | /api/exclusions/* | 対戦除外設定 |
| reports.py | /api/reports/* | PDF/Excel出力 |

### schemas/ - Pydanticスキーマ（15ファイル）

各モデルに対応したリクエスト/レスポンススキーマ

### services/ - ビジネスロジック

| ファイル | 説明 |
|----------|------|
| standing_service.py | 順位計算ロジック |

### utils/ - ユーティリティ

| ファイル | 説明 |
|----------|------|
| auth.py | JWT認証、パスワードハッシュ |
| websocket.py | WebSocket管理 |

## 3.2 フロントエンド サブモジュール

### pages/ - ページコンポーネント（12+2ファイル）

| ファイル | パス | 説明 |
|----------|------|------|
| Login.tsx | /login | ログイン画面 |
| Dashboard.tsx | / | ダッシュボード |
| TeamManagement.tsx | /teams | チーム管理 |
| PlayerManagement.tsx | /players | 選手管理 |
| MatchSchedule.tsx | /schedule | 日程管理 |
| MatchResult.tsx | /results | 結果入力 |
| MatchApproval.tsx | /approval | 結果承認 |
| Standings.tsx | /standings | 順位表 |
| ScorerRanking.tsx | /scorers | 得点ランキング |
| ExclusionSettings.tsx | /exclusions | 対戦除外設定 |
| Reports.tsx | /reports | レポート出力 |
| Settings.tsx | /settings | システム設定 |
| public/PublicStandings.tsx | /public/standings | 公開順位表 |
| public/PublicMatchList.tsx | /public/matches | 公開試合一覧 |

### features/ - 機能モジュール（9モジュール）

各モジュール構成: types.ts, api.ts, hooks.ts, index.ts

| モジュール | 説明 |
|------------|------|
| tournaments | 大会管理 |
| teams | チーム管理 |
| players | 選手管理 |
| staff | スタッフ管理 |
| venues | 会場管理 |
| matches | 試合管理 |
| standings | 順位表 |
| exclusions | 対戦除外 |
| reports | レポート |

### components/ - コンポーネント

| ディレクトリ | 説明 |
|--------------|------|
| ui/ | Button, Card, Modal, Table, Select, Badge等 |
| layout/ | Layout, Header, Sidebar |
| auth/ | RequireAuth（権限制御） |
| approval/ | 承認パネル |
| pwa/ | オフライン対応UI |
| common/ | LoadingSpinner, ConnectionStatus |
| FinalsBracket.tsx | 決勝トーナメント表示 |
| DraggableMatchList.tsx | D&D試合リスト |

### core/ - コアモジュール

| ディレクトリ | 説明 |
|--------------|------|
| http/ | HTTPクライアント、インターセプター |
| auth/ | 認証管理 |
| sync/ | オフライン同期 |
| config/ | 設定管理 |
| errors/ | エラーハンドリング |

### stores/ - 状態管理（Zustand）

| ファイル | 説明 |
|----------|------|
| authStore.ts | 認証状態 |
| appStore.ts | アプリ全体状態 |
| teamStore.ts | チーム状態 |
| matchStore.ts | 試合状態 |
| standingStore.ts | 順位表状態 |

### hooks/ - カスタムフック

| ファイル | 説明 |
|----------|------|
| useApi.ts | API呼び出し |
| usePWA.ts | PWA同期状態 |
| useWebSocket.ts | WebSocket接続 |
| useRealtimeUpdates.ts | リアルタイム更新 |

## 3.3 外部サブモジュール

### agent-UrawaCup/ - AI自動生成エージェント

| ファイル | 説明 |
|----------|------|
| main.py | CLIエントリーポイント |
| config.py | 設定 |
| agents/code_generator.py | コード生成 |
| agents/requirement_analyzer.py | 要件分析 |
| agents/architecture_validator.py | アーキテクチャ検証 |
| agents/issue_manager.py | Issue管理 |
| agents/auto_loop_agent.py | 自動生成ループ |
| agents/uncertainty_guard.py | 不確実性検出 |

### requirement-checker-sdk/ - 要件チェッカー

| ファイル | 説明 |
|----------|------|
| main.py | メインチェッカー |
| src/requirements_data.py | 要件定義データ |
| src/code_checker.py | コードスキャン |

---

# 4. 画面一覧

## 4.1 管理者向け画面

| 画面ID | 画面名 | URL | 実装 |
|--------|--------|-----|------|
| S-01 | ログイン | /login | ✅ |
| S-02 | ダッシュボード | / | ✅ |
| S-03 | チーム管理 | /teams | ✅ |
| S-04 | 選手管理 | /players | ✅ |
| S-05 | 日程管理 | /schedule | ✅ |
| S-06 | 結果入力 | /results | ✅ |
| S-07 | 結果承認 | /approval | ✅ |
| S-08 | 順位表 | /standings | ✅ |
| S-09 | 得点ランキング | /scorers | ✅ |
| S-10 | 対戦除外設定 | /exclusions | ✅ |
| S-11 | レポート | /reports | ✅ |
| S-12 | 設定 | /settings | ✅ |

## 4.2 公開画面

| 画面ID | 画面名 | URL | 実装 |
|--------|--------|-----|------|
| P-01 | 公開順位表 | /public/standings | ✅ |
| P-02 | 公開試合一覧 | /public/matches | ✅ |

---

# 5. API一覧

## 5.1 認証 API

| メソッド | パス | 説明 | 実装 |
|----------|------|------|------|
| POST | /api/auth/login | ログイン | ✅ |
| POST | /api/auth/logout | ログアウト | ✅ |
| GET | /api/auth/me | 現在のユーザー | ✅ |
| POST | /api/auth/refresh | トークンリフレッシュ | ✅ |

## 5.2 大会 API

| メソッド | パス | 説明 | 実装 |
|----------|------|------|------|
| GET | /api/tournaments | 一覧取得 | ✅ |
| POST | /api/tournaments | 作成 | ✅ |
| GET | /api/tournaments/{id} | 詳細取得 | ✅ |
| PATCH | /api/tournaments/{id} | 更新 | ✅ |
| DELETE | /api/tournaments/{id} | 削除 | ✅ |

## 5.3 チーム API

| メソッド | パス | 説明 | 実装 |
|----------|------|------|------|
| GET | /api/teams | 一覧取得 | ✅ |
| POST | /api/teams | 作成 | ✅ |
| GET | /api/teams/{id} | 詳細取得 | ✅ |
| PATCH | /api/teams/{id} | 更新 | ✅ |
| DELETE | /api/teams/{id} | 削除 | ✅ |
| POST | /api/teams/import | CSVインポート | ✅ |

## 5.4 選手 API

| メソッド | パス | 説明 | 実装 |
|----------|------|------|------|
| GET | /api/players | 一覧取得 | ✅ |
| GET | /api/teams/{id}/players | チーム別選手 | ✅ |
| POST | /api/players | 作成 | ✅ |
| PATCH | /api/players/{id} | 更新 | ✅ |
| DELETE | /api/players/{id} | 削除 | ✅ |
| GET | /api/players/suggestions | サジェスト | ✅ |

## 5.5 スタッフ API

| メソッド | パス | 説明 | 実装 |
|----------|------|------|------|
| GET | /api/staff | 一覧取得 | ✅ |
| GET | /api/teams/{id}/staff | チーム別スタッフ | ✅ |
| POST | /api/staff | 作成 | ✅ |
| PATCH | /api/staff/{id} | 更新 | ✅ |
| DELETE | /api/staff/{id} | 削除 | ✅ |

## 5.6 会場 API

| メソッド | パス | 説明 | 実装 |
|----------|------|------|------|
| GET | /api/venues | 一覧取得 | ✅ |
| POST | /api/venues | 作成 | ✅ |
| PATCH | /api/venues/{id} | 更新 | ✅ |
| DELETE | /api/venues/{id} | 削除 | ✅ |

## 5.7 試合 API

| メソッド | パス | 説明 | 実装 |
|----------|------|------|------|
| GET | /api/matches | 一覧取得 | ✅ |
| GET | /api/matches/{id} | 詳細取得 | ✅ |
| PUT | /api/matches/{id} | 更新 | ✅ |
| PUT | /api/matches/{id}/score | スコア入力 | ✅ |
| POST | /api/matches/{id}/lock | ロック取得 | ✅ |
| DELETE | /api/matches/{id}/lock | ロック解除 | ✅ |
| POST | /api/matches/generate-schedule/{id} | 予選日程生成 | ✅ |
| POST | /api/matches/generate-finals/{id} | 決勝T生成 | ✅ |
| POST | /api/matches/generate-training/{id} | 研修試合生成 | ✅ |

## 5.8 順位表 API

| メソッド | パス | 説明 | 実装 |
|----------|------|------|------|
| GET | /api/standings | 順位表取得 | ✅ |
| POST | /api/standings/recalculate/{id} | 再計算 | ✅ |
| GET | /api/standings/scorers | 得点ランキング | ✅ |

## 5.9 対戦除外 API

| メソッド | パス | 説明 | 実装 |
|----------|------|------|------|
| GET | /api/exclusions | 一覧取得 | ✅ |
| POST | /api/exclusions | 作成 | ✅ |
| DELETE | /api/exclusions/{id} | 削除 | ✅ |

## 5.10 レポート API

| メソッド | パス | 説明 | 実装 |
|----------|------|------|------|
| GET | /api/reports/daily | 日次報告書 | ✅ |
| GET | /api/reports/standings | 順位表PDF | ✅ |
| GET | /api/reports/export/final-day-schedule | 最終日組み合わせ | ✅ |
| GET | /api/reports/export/final-result | 最終結果 | ✅ |
| GET | /api/reports/export/group-standings | グループ順位表 | ✅ |

---

# 6. データモデル

## 6.1 ER図

```
Tournament 1:N Group
Tournament 1:N Team
Tournament 1:N Venue
Tournament 1:N Match
Tournament 1:N Standing
Tournament 1:N ExclusionPair
Tournament 1:N TournamentAward
Tournament 1:N ReportRecipient

Group 1:N Team
Group 1:N Match (groupId)

Team 1:N Player
Team 1:N Staff
Team 1:N TeamUniform
Team 1:N Match (home/away)
Team 1:N Goal

Match 1:N Goal
Match N:1 Venue
Match N:1 User (lockedBy, enteredBy, approvedBy)

Player 1:N Goal (nullable)
Player 1:N TournamentAward
```

## 6.2 主要テーブル

| テーブル | 説明 | レコード目安 |
|----------|------|--------------|
| tournaments | 大会情報 | 1件/年 |
| groups | グループ（A〜D） | 4件/大会 |
| teams | チーム | 24件/大会 |
| players | 選手 | 600-1200件/大会 |
| staff | スタッフ | 48-100件/大会 |
| team_uniforms | ユニフォーム | 96件/大会 |
| venues | 会場 | 4-5件/大会 |
| matches | 試合 | 72件/大会 |
| goals | 得点 | 200件/大会 |
| standings | 順位表 | 24件/大会 |
| exclusion_pairs | 対戦除外 | 12件/大会 |
| users | ユーザー | 5-10件 |

---

# 7. 実装状況

## 7.1 サマリー

| カテゴリ | 完了 | 一部 | 未実装 | 完了率 |
|----------|------|------|--------|--------|
| 大会管理 | 3 | 0 | 0 | 100% |
| チーム管理 | 5 | 0 | 0 | 100% |
| 選手管理 | 4 | 1 | 0 | 90% |
| スタッフ管理 | 2 | 0 | 0 | 100% |
| 会場管理 | 3 | 0 | 0 | 100% |
| 日程管理 | 6 | 0 | 0 | 100% |
| 結果入力 | 5 | 0 | 0 | 100% |
| 順位・統計 | 4 | 0 | 0 | 100% |
| レポート | 5 | 0 | 0 | 100% |
| 公開機能 | 3 | 0 | 0 | 100% |
| PWA/オフライン | 4 | 0 | 0 | 100% |
| **合計** | **44** | **1** | **0** | **98%** |

## 7.2 未完了・一部実装の項目

| ID | 機能 | ステータス | 説明 |
|----|------|------------|------|
| F-22 | 参加申込書形式インポート | ⚠️ 一部実装 | CSVは対応、Excel参加申込書の2列構成パーサーは未実装 |

## 7.3 フェーズ別実装状況

### Phase 1: MINI（信頼できる計算機）
- ✅ チーム・グループ管理
- ✅ 試合結果入力
- ✅ 順位表自動計算
- ✅ 基礎エクスポート

### Phase 2: MIDDLE（業務効率化ツール）
- ✅ 公式帳票出力（PDF/Excel）
- ✅ 分散入力対応
- ✅ 結果承認フロー
- ✅ 日程調整アシスト
- ✅ 決勝Tマッチング

### Phase 3: MAX（大会プラットフォーム）
- ✅ パブリックビューイング
- ✅ 詳細スタッツ（得点者記録）
- ✅ オフライン対応（PWA）
- ⚠️ 大会アーカイブ（基本実装済、UI改善余地あり）

---

# 改訂履歴

| バージョン | 日付 | 変更内容 |
|------------|------|----------|
| 2.0 | 2026-01-01 | 初版作成 |
| 2.1 | 2026-01-03 | サブモジュール構成追加、実装状況更新 |
