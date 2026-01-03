# TournaMate - トーナメント管理システム 設計書

**バージョン**: 1.0  
**最終更新**: 2026-01-02  
**ライセンス**: MIT License（完全フリー・オープンソース）  
**配布形式**: PWA（Progressive Web App）

---

# 目次

1. [プロジェクト概要](#1-プロジェクト概要)
2. [機能要件](#2-機能要件)
3. [システム設計](#3-システム設計)
4. [データベース設計](#4-データベース設計)
5. [API設計](#5-api設計)
6. [PWA実装](#6-pwa実装)
7. [拡張性設計](#7-拡張性設計)
8. [ディレクトリ構成](#8-ディレクトリ構成)
9. [デプロイ手順](#9-デプロイ手順)
10. [開発ロードマップ](#10-開発ロードマップ)

---

# 1. プロジェクト概要

## 1.1 システム名

**TournaMate** - あなたの大会運営パートナー

## 1.2 目的

サッカー等のスポーツ大会の運営を効率化するWebアプリケーション。
予選リーグ・決勝トーナメントの日程生成、結果入力、順位計算、報告書出力を自動化。

## 1.3 特徴

- **完全無料・オープンソース**（MIT License）
- **PWA対応** - インストール可能、オフライン対応
- **セルフホスト** - 各団体が自分でデプロイ・運用
- **汎用設計** - 様々な大会形式に対応可能

## 1.4 対象ユーザー

| ユーザー | 役割 |
|---------|------|
| 管理者 | 大会設定、チーム登録、日程生成、報告書出力 |
| 会場担当者 | 試合結果入力 |
| 閲覧者（一般） | 順位表・試合結果の閲覧 |

## 1.5 技術スタック

| 層 | 技術 |
|----|------|
| フロントエンド | React 18 + TypeScript + Vite |
| スタイリング | Tailwind CSS |
| 状態管理 | Zustand |
| バックエンド | FastAPI (Python 3.11+) |
| データベース | PostgreSQL / SQLite |
| 認証 | JWT |
| PWA | Workbox |
| デプロイ | Vercel + Railway / Docker |

---

# 2. 機能要件

## 2.1 機能一覧

### 大会管理

| ID | 機能 | 説明 |
|----|------|------|
| F-01 | 大会作成 | 名称、日程、形式を設定 |
| F-02 | 大会設定 | 試合時間、インターバル等の設定 |
| F-03 | グループ設定 | グループ数、チーム数の設定 |
| F-04 | 会場設定 | 会場の登録、グループへの紐付け |
| F-05 | 最終日形式設定 | トーナメント/順位別リーグ等の選択 |

### チーム管理

| ID | 機能 | 説明 |
|----|------|------|
| F-10 | チーム登録 | チーム名、略称、区分の登録 |
| F-11 | チーム編集 | チーム情報の編集 |
| F-12 | グループ配置 | チームのグループ振り分け |
| F-13 | チームインポート | CSV/Excelからの一括登録 |

### 選手管理

| ID | 機能 | 説明 |
|----|------|------|
| F-20 | 選手登録 | 背番号、氏名、フリガナの登録 |
| F-21 | 選手編集 | 選手情報の編集 |
| F-22 | 選手インポート | CSV/Excelからの一括登録 |

### 日程管理

| ID | 機能 | 説明 |
|----|------|------|
| F-30 | 除外ペア設定 | 対戦しない組み合わせの設定 |
| F-31 | 予選日程生成 | 自動で予選リーグ日程を生成 |
| F-32 | 日程編集 | 試合日時、会場の手動調整 |
| F-33 | 最終日日程生成 | 予選結果に基づく最終日日程生成 |

### 結果入力

| ID | 機能 | 説明 |
|----|------|------|
| F-40 | スコア入力 | 前半/後半のスコア入力 |
| F-41 | PK戦入力 | PK戦のスコア入力 |
| F-42 | 得点者入力 | 得点者名、時間の入力 |
| F-43 | 得点者サジェスト | 選手一覧からの選択 |
| F-44 | 自由入力 | 選手一覧にない場合の自由入力 |
| F-45 | 排他ロック | 編集中の他ユーザーブロック |
| F-46 | 楽観的ロック | 同時更新時の競合検出 |

### 順位計算

| ID | 機能 | 説明 |
|----|------|------|
| F-50 | 自動順位計算 | 勝点→得失点差→総得点→直接対決→抽選 |
| F-51 | リアルタイム更新 | 結果入力時に即時反映 |
| F-52 | 順位確定 | 同順位の抽選結果入力 |

### 報告書

| ID | 機能 | 説明 |
|----|------|------|
| F-60 | 報告書生成 | 日付・会場別のPDF生成 |
| F-61 | 得点経過表示 | 時間順の得点経過 |
| F-62 | 送信先表示 | 報告書の送信先リスト |

### 公開機能

| ID | 機能 | 説明 |
|----|------|------|
| F-70 | 公開順位表 | 認証不要の順位表閲覧 |
| F-71 | 公開試合一覧 | 認証不要の試合結果閲覧 |
| F-72 | リアルタイム更新 | WebSocketによる自動更新 |

### オフライン対応

| ID | 機能 | 説明 |
|----|------|------|
| F-80 | オフライン入力 | 電波がなくても入力可能 |
| F-81 | 自動同期 | オンライン復帰時に自動同期 |
| F-82 | 競合解決 | 同期時の競合検出・解決UI |
| F-83 | 未同期表示 | 未同期データのバッジ表示 |

## 2.2 画面一覧

| 画面 | URL | 認証 |
|------|-----|------|
| ログイン | `/login` | 不要 |
| ダッシュボード | `/admin/dashboard` | 必要 |
| チーム管理 | `/admin/teams` | 必要 |
| 選手管理 | `/admin/players` | 必要 |
| 日程管理 | `/admin/schedule` | 必要 |
| 結果入力 | `/admin/results` | 必要 |
| 順位表（管理） | `/admin/standings` | 必要 |
| 報告書 | `/admin/reports` | 必要 |
| 設定 | `/admin/settings` | 必要 |
| 公開順位表 | `/standings` | 不要 |
| 公開試合一覧 | `/matches` | 不要 |

---

# 3. システム設計

## 3.1 アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                        クライアント                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 管理者      │  │ 会場担当者  │  │ 閲覧者      │        │
│  │ (PC)       │  │ (スマホ)    │  │ (スマホ)    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │               │               │                 │
│         └───────────────┼───────────────┘                 │
│                         │                                  │
│  ┌──────────────────────┴──────────────────────┐          │
│  │              PWA (React + Vite)              │          │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────┐ │          │
│  │  │ オフライン │ │ IndexedDB │ │ Service  │ │          │
│  │  │ キュー    │ │ キャッシュ │ │ Worker   │ │          │
│  │  └────────────┘ └────────────┘ └──────────┘ │          │
│  └──────────────────────┬──────────────────────┘          │
└─────────────────────────┼───────────────────────────────────┘
                          │ HTTPS
┌─────────────────────────┼───────────────────────────────────┐
│                         │                                   │
│  ┌──────────────────────┴──────────────────────┐           │
│  │              FastAPI Backend                 │           │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────┐ │           │
│  │  │ REST API  │ │ WebSocket │ │ 認証     │ │           │
│  │  │ エンドポイント│ │ (リアルタイム)│ │ (JWT)   │ │           │
│  │  └────────────┘ └────────────┘ └──────────┘ │           │
│  └──────────────────────┬──────────────────────┘           │
│                         │                                   │
│  ┌──────────────────────┴──────────────────────┐           │
│  │              PostgreSQL / SQLite             │           │
│  └─────────────────────────────────────────────┘           │
│                        サーバー                             │
└─────────────────────────────────────────────────────────────┘
```

## 3.2 コア原則

| 原則 | 実装 |
|------|------|
| Single Source of Truth | HTTPクライアント、AuthManagerは1つのみ |
| Contract First | OpenAPIからTypeScript型を自動生成 |
| Explicit Dependencies | DI/Factory パターン |
| Offline First | SyncQueue + IndexedDB |

## 3.3 HTTPクライアント（シングルトン）

```typescript
// src/core/http/client.ts
class HttpClient {
  private static instance: HttpClient;
  private client: AxiosInstance;

  private constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || '/api',
      timeout: 30000,
    });
    this.setupInterceptors();
  }

  public static getInstance(): HttpClient {
    if (!HttpClient.instance) {
      HttpClient.instance = new HttpClient();
    }
    return HttpClient.instance;
  }

  private setupInterceptors(): void {
    // 認証ヘッダー
    this.client.interceptors.request.use(authInterceptor);
    // エラー正規化
    this.client.interceptors.response.use(null, errorInterceptor);
    // 命名規則変換（snake_case ↔ camelCase）
    this.client.interceptors.response.use(transformInterceptor);
  }
}

export const httpClient = HttpClient.getInstance();
```

## 3.4 認証管理（AuthManager）

```typescript
// src/core/auth/manager.ts
class AuthManager {
  private static instance: AuthManager;
  private accessToken: string | null = null;

  public static getInstance(): AuthManager { ... }
  public getAccessToken(): string | null { ... }
  public setTokens(access: string, refresh?: string): void { ... }
  public clearTokens(): void { ... }
  public isAuthenticated(): boolean { ... }
}

export const authManager = AuthManager.getInstance();
```

## 3.5 エラーハンドリング

```typescript
// src/core/errors/types.ts
interface AppError {
  code: ErrorCode;
  message: string;
  status?: number;
  details?: Record<string, unknown>;
  retryable: boolean;
}

type ErrorCode =
  | 'NETWORK_ERROR'
  | 'UNAUTHORIZED'
  | 'FORBIDDEN'
  | 'NOT_FOUND'
  | 'VALIDATION_ERROR'
  | 'VERSION_CONFLICT'
  | 'LOCK_CONFLICT'
  | 'SERVER_ERROR'
  | 'OFFLINE'
  | 'UNKNOWN';
```

---

# 4. データベース設計

## 4.1 ER図

```
tournaments
    |
    +-- tournament_stages (予選, 1位リーグ, ...)
    |       |
    |       +-- stage_rules
    |
    +-- groups (A, B, C, D, ...)
    |       |
    |       +-- teams
    |       |       |
    |       |       +-- players
    |       |
    |       +-- standings
    |       |
    |       +-- exclusion_pairs
    |
    +-- venues
    |
    +-- matches
            |
            +-- goals
            |
            +-- match_locks
```

## 4.2 テーブル定義

### tournaments（大会）

```sql
CREATE TABLE tournaments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    edition INTEGER,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    num_days INTEGER DEFAULT 3,
    num_groups INTEGER DEFAULT 4,
    teams_per_group INTEGER DEFAULT 6,
    matches_per_team INTEGER DEFAULT 4,
    match_duration INTEGER DEFAULT 50,
    half_duration INTEGER DEFAULT 25,
    interval_minutes INTEGER DEFAULT 15,
    preliminary_format VARCHAR(20) DEFAULT 'modified',
    final_day_format VARCHAR(30) DEFAULT 'tournament_and_training',
    settings JSONB,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### teams（チーム）

```sql
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id),
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(20),
    team_type VARCHAR(20) DEFAULT 'invited',
    is_venue_host BOOLEAN DEFAULT FALSE,
    group_id VARCHAR(10),
    group_order INTEGER,
    prefecture VARCHAR(20),
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### players（選手）

```sql
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    number INTEGER,
    name VARCHAR(100) NOT NULL,
    name_kana VARCHAR(100),
    name_normalized VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_players_team ON players(team_id);
CREATE INDEX idx_players_name ON players(name_normalized);
```

### matches（試合）

```sql
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id),
    stage_id INTEGER REFERENCES tournament_stages(id),
    group_id VARCHAR(10),
    venue_id INTEGER REFERENCES venues(id),
    home_team_id INTEGER NOT NULL REFERENCES teams(id),
    away_team_id INTEGER NOT NULL REFERENCES teams(id),
    match_date DATE NOT NULL,
    match_time TIME,
    match_order INTEGER,
    stage VARCHAR(30) DEFAULT 'preliminary',
    status VARCHAR(20) DEFAULT 'scheduled',
    home_score_half1 INTEGER,
    home_score_half2 INTEGER,
    home_score_total INTEGER,
    away_score_half1 INTEGER,
    away_score_half2 INTEGER,
    away_score_total INTEGER,
    home_pk INTEGER,
    away_pk INTEGER,
    has_penalty_shootout BOOLEAN DEFAULT FALSE,
    entered_by INTEGER REFERENCES users(id),
    entered_at TIMESTAMP,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_matches_tournament_date ON matches(tournament_id, match_date);
CREATE INDEX idx_matches_status ON matches(status);
```

### match_locks（排他ロック）

```sql
CREATE TABLE match_locks (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL UNIQUE REFERENCES matches(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
```

### goals（得点）

```sql
CREATE TABLE goals (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    player_id INTEGER REFERENCES players(id),
    scorer_name VARCHAR(100) NOT NULL,
    minute INTEGER,
    half INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_goals_match ON goals(match_id);
```

### standings（順位表）

```sql
CREATE TABLE standings (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id),
    stage_id INTEGER REFERENCES tournament_stages(id),
    group_id VARCHAR(10) NOT NULL,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    rank INTEGER,
    played INTEGER DEFAULT 0,
    won INTEGER DEFAULT 0,
    drawn INTEGER DEFAULT 0,
    lost INTEGER DEFAULT 0,
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    goal_difference INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    rank_reason VARCHAR(100),
    version INTEGER DEFAULT 1,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tournament_id, stage_id, group_id, team_id)
);

CREATE INDEX idx_standings_rank ON standings(tournament_id, group_id, rank);
```

### exclusion_pairs（除外ペア）

```sql
CREATE TABLE exclusion_pairs (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id),
    group_id VARCHAR(10) NOT NULL,
    team1_id INTEGER NOT NULL REFERENCES teams(id),
    team2_id INTEGER NOT NULL REFERENCES teams(id),
    reason VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tournament_id, team1_id, team2_id)
);
```

### sync_queue（オフライン同期キュー）

```sql
CREATE TABLE sync_queue (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(36) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    operation VARCHAR(20) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP
);
```

---

# 5. API設計

## 5.1 認証

```yaml
POST /api/auth/login
  Request: { email, password }
  Response: { accessToken, refreshToken, user }

POST /api/auth/refresh
  Request: { refreshToken }
  Response: { accessToken }

POST /api/auth/logout
  Response: { success }
```

## 5.2 大会

```yaml
GET    /api/tournaments                    # 一覧
POST   /api/tournaments                    # 作成
GET    /api/tournaments/{id}               # 取得
GET    /api/tournaments/by-slug/{slug}     # スラッグで取得
PATCH  /api/tournaments/{id}               # 更新
DELETE /api/tournaments/{id}               # 削除
```

## 5.3 チーム

```yaml
GET    /api/tournaments/{tid}/teams        # 一覧
POST   /api/tournaments/{tid}/teams        # 作成
GET    /api/teams/{id}                     # 取得
PATCH  /api/teams/{id}                     # 更新
DELETE /api/teams/{id}                     # 削除
POST   /api/tournaments/{tid}/teams/import # CSV/Excelインポート
```

## 5.4 選手

```yaml
GET    /api/teams/{tid}/players            # 一覧
POST   /api/teams/{tid}/players            # 作成
GET    /api/players/{id}                   # 取得
PATCH  /api/players/{id}                   # 更新
DELETE /api/players/{id}                   # 削除
POST   /api/teams/{tid}/players/import     # インポート
```

## 5.5 試合

```yaml
GET    /api/tournaments/{tid}/matches      # 一覧
POST   /api/tournaments/{tid}/matches/generate-preliminary  # 予選日程生成
POST   /api/tournaments/{tid}/matches/generate-final        # 最終日日程生成

GET    /api/matches/{id}                   # 取得
PATCH  /api/matches/{id}                   # 更新

POST   /api/matches/{id}/lock              # 排他ロック取得
DELETE /api/matches/{id}/lock              # 排他ロック解放

PUT    /api/matches/{id}/score             # スコア入力
  Request: { homeScoreHalf1, homeScoreHalf2, ..., goals[], version }
  Response: { match, newVersion }
```

## 5.6 順位表

```yaml
GET    /api/tournaments/{tid}/standings    # 全グループ
GET    /api/tournaments/{tid}/standings/{groupId}  # グループ別
POST   /api/tournaments/{tid}/standings/recalculate  # 再計算
```

## 5.7 報告書

```yaml
POST   /api/tournaments/{tid}/reports/generate
  Request: { date, venueId, format }
  Response: { jobId }

GET    /api/reports/jobs/{jobId}
  Response: { status, progress, url }
```

## 5.8 公開API（認証不要）

```yaml
GET    /api/public/tournaments/{slug}/standings
GET    /api/public/tournaments/{slug}/matches
GET    /api/public/tournaments/{slug}/matches/{date}
```

---

# 6. PWA実装

## 6.1 manifest.json

```json
{
  "name": "TournaMate - 大会運営システム",
  "short_name": "TournaMate",
  "description": "サッカー大会の運営を効率化するアプリ",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#1a56db",
  "orientation": "portrait-primary",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

## 6.2 ServiceWorker（Workbox）

```typescript
// sw.ts
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { NetworkFirst, CacheFirst, StaleWhileRevalidate } from 'workbox-strategies';

// プリキャッシュ
precacheAndRoute(self.__WB_MANIFEST);

// API: ネットワーク優先
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({ cacheName: 'api-cache', networkTimeoutSeconds: 5 })
);

// 静的アセット: キャッシュ優先
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({ cacheName: 'image-cache' })
);

// HTML: SWR
registerRoute(
  ({ request }) => request.mode === 'navigate',
  new StaleWhileRevalidate({ cacheName: 'html-cache' })
);
```

## 6.3 オフライン同期キュー

```typescript
// src/core/sync/queue.ts
import { openDB } from 'idb';

export class SyncQueue {
  private db: IDBDatabase | null = null;

  async add(request: PendingRequest): Promise<string> {
    const id = crypto.randomUUID();
    await this.db!.add('pending-requests', { ...request, id, createdAt: new Date() });
    
    if ('serviceWorker' in navigator && 'sync' in registration) {
      await registration.sync.register('sync-pending');
    }
    return id;
  }

  async sync(): Promise<SyncResult[]> {
    const pending = await this.getPending();
    const results: SyncResult[] = [];
    
    for (const item of pending) {
      try {
        const response = await httpClient.request(item);
        await this.remove(item.id);
        results.push({ id: item.id, status: 'synced' });
      } catch (error) {
        if (error.code === 'VERSION_CONFLICT') {
          results.push({ id: item.id, status: 'conflict', serverData: error.details });
        } else {
          results.push({ id: item.id, status: 'error', error });
        }
      }
    }
    return results;
  }
}
```

## 6.4 インストールプロンプト

```tsx
// src/components/InstallPrompt.tsx
export function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);

  useEffect(() => {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
    });
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') setDeferredPrompt(null);
  };

  if (!deferredPrompt) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 bg-blue-600 text-white p-4 rounded-lg">
      <p className="font-bold">TournaMateをインストール</p>
      <button onClick={handleInstall} className="mt-2 px-4 py-2 bg-white text-blue-600 rounded">
        インストール
      </button>
    </div>
  );
}
```

---

# 7. 拡張性設計

## 7.1 可変項目

| 項目 | 現在のデフォルト | 将来対応 |
|------|----------------|----------|
| 試合日数 | 3日間 | N日間 |
| グループ数 | 4 | 2〜8 |
| チーム数/グループ | 6 | 4〜8 |
| 予選形式 | 変則リーグ | 総当たり / 変則 |
| 最終日形式 | トーナメント+研修 | 順位別リーグ / カスタム |

## 7.2 最終日形式オプション

```typescript
enum FinalDayFormat {
  TOURNAMENT_AND_TRAINING = 'tournament_and_training',  // 現行
  RANK_LEAGUES = 'rank_leagues',                        // 順位別リーグ
  FULL_KNOCKOUT = 'full_knockout',                      // フルトーナメント
  CUSTOM = 'custom',                                    // カスタム
}
```

## 7.3 ステージ設定

```typescript
interface TournamentStage {
  id: number;
  name: string;                  // "予選リーグ", "1位リーグ", ...
  stageType: StageType;          // preliminary, final_league, knockout, training
  dayNumbers: number[];          // 実施日
  isRanked: boolean;             // 順位を決定するか
  includeInReport: boolean;      // 報告書に含めるか
  rules: StageRuleConfig;
}

interface StageRuleConfig {
  qualification?: {
    fromStage: string;
    ranks: number[];
  };
  matchup?: {
    type: 'round_robin' | 'knockout' | 'same_rank';
    avoidPreviousOpponent?: boolean;
  };
}
```

---

# 8. ディレクトリ構成

```
tournamate/
├── README.md
├── LICENSE                          # MIT License
├── docker-compose.yml
│
├── docs/
│   ├── INSTALL.md                   # インストール手順
│   ├── DEPLOY_VERCEL.md             # Vercelデプロイ手順
│   ├── DEPLOY_RAILWAY.md            # Railwayデプロイ手順
│   ├── DEPLOY_DOCKER.md             # Dockerデプロイ手順
│   ├── USER_GUIDE.md                # 使い方ガイド
│   └── API.md                       # API仕様
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       │
│       ├── core/                    # 基盤
│       │   ├── http/
│       │   │   ├── client.ts        # HTTPクライアント
│       │   │   └── interceptors/
│       │   ├── auth/
│       │   │   ├── manager.ts       # AuthManager
│       │   │   └── store.ts
│       │   ├── errors/
│       │   │   ├── types.ts
│       │   │   └── handler.ts
│       │   ├── sync/
│       │   │   ├── queue.ts
│       │   │   └── storage.ts
│       │   └── websocket/
│       │
│       ├── features/                # 機能別
│       │   ├── tournaments/
│       │   ├── teams/
│       │   ├── players/
│       │   ├── matches/
│       │   ├── standings/
│       │   ├── exclusions/
│       │   └── reports/
│       │
│       ├── pages/
│       │   ├── Login.tsx
│       │   ├── admin/
│       │   └── public/
│       │
│       ├── components/
│       │   ├── Layout.tsx
│       │   ├── InstallPrompt.tsx
│       │   └── ui/
│       │
│       └── shared/
│           ├── types/
│           └── utils/
│
├── backend/
│   ├── pyproject.toml
│   ├── requirements.txt
│   │
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   │
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── tournaments.py
│   │   │   ├── teams.py
│   │   │   ├── players.py
│   │   │   ├── matches.py
│   │   │   ├── standings.py
│   │   │   └── reports.py
│   │   │
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   │
│   └── migrations/
│
└── deploy/
    ├── vercel.json
    ├── railway.json
    └── Dockerfile
```

---

# 9. デプロイ手順

## 9.1 Vercel + Railway（推奨）

### 所要時間: 約15分

```
1. GitHubでリポジトリをFork

2. フロントエンド（Vercel）
   - vercel.com にログイン
   - "Import Project" → Forkしたリポジトリ選択
   - Root Directory: frontend
   - Deploy

3. バックエンド + DB（Railway）
   - railway.app にログイン
   - "New Project" → "Deploy from GitHub"
   - リポジトリ選択、backend ディレクトリ
   - PostgreSQLを追加
   - 環境変数設定

4. 環境変数設定
   【Vercel】
   - VITE_API_URL = https://your-backend.railway.app

   【Railway】
   - DATABASE_URL = (自動設定)
   - SECRET_KEY = (ランダム文字列)
   - CORS_ORIGINS = https://your-frontend.vercel.app

5. 完了！
```

## 9.2 Docker Compose（ローカル/VPS）

```bash
git clone https://github.com/your-org/tournamate.git
cd tournamate
cp .env.example .env
# .env を編集
docker-compose up -d
# → http://localhost:3000
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/tournamate
    depends_on:
      - db

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=tournamate

volumes:
  postgres_data:
```

---

# 10. 開発ロードマップ

## Phase 1: MVP（v1.0）

```
目標: 浦和カップで実用できるレベル

□ 認証（ログイン/ログアウト）
□ チーム管理（CRUD）
□ 選手管理（CRUD）
□ 予選日程生成（変則リーグ）
□ 結果入力（スコア、得点者）
□ 順位計算（自動）
□ 公開順位表
□ PWA基本対応
```

## Phase 2: 安定化（v1.1）

```
□ 排他ロック
□ 楽観的ロック
□ オフライン入力
□ 競合解決UI
□ 報告書PDF出力
□ WebSocketリアルタイム更新
```

## Phase 3: 拡張（v2.0）

```
□ 大会設定の外部化
□ グループ数・チーム数の可変化
□ 最終日形式の選択
□ 順位別リーグ対応
□ 大会テンプレート
```

---

# 付録

## A. 命名規則

| 場所 | 規則 | 例 |
|------|------|-----|
| バックエンドAPI | camelCase | tournamentId, homeScore |
| データベース | snake_case | tournament_id, home_score |
| フロントエンド変数 | camelCase | tournamentId, homeScore |
| CSSクラス | kebab-case | match-card, score-input |
| ファイル名（コンポーネント） | PascalCase | TeamManagement.tsx |
| ファイル名（hooks） | camelCase | useMatches.ts |

## B. ブランチ戦略

```
main        ← 本番
  └── develop    ← 開発
        ├── feature/xxx    ← 機能追加
        ├── fix/xxx        ← バグ修正
        └── refactor/xxx   ← リファクタ
```

## C. ライセンス

```
MIT License

Copyright (c) 2025 TournaMate Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

# 11. セキュリティ要件

## 11.1 認証・認可

| 項目 | 仕様 |
|------|------|
| 認証方式 | JWT (JSON Web Token) |
| アクセストークン有効期限 | 30分 |
| リフレッシュトークン有効期限 | 7日 |
| パスワードハッシュ | bcrypt (cost factor: 12) |
| セッション管理 | メモリ保持（XSS対策）|

## 11.2 権限モデル

```
roles:
  admin:
    - 全機能へのフルアクセス
    - ユーザー管理
    - 大会設定変更
    - 結果承認/却下

  venue_staff:
    - 担当会場の試合結果入力
    - 担当会場の選手情報閲覧
    - 順位表閲覧

  staff:
    - 試合結果閲覧
    - 順位表閲覧
```

## 11.3 セキュリティ対策

| 脅威 | 対策 |
|------|------|
| XSS | CSP設定、HTML エスケープ、React の自動エスケープ |
| CSRF | SameSite Cookie、CORS設定 |
| SQLインジェクション | SQLAlchemy ORM使用、パラメータバインド |
| 認証情報漏洩 | トークンはメモリ保持、HTTPS必須 |
| ブルートフォース | レートリミット（5回/分）、アカウントロック |

## 11.4 データ保護

```yaml
sensitive_data:
  - パスワード: bcryptハッシュで保存
  - アクセストークン: メモリのみ、永続化しない
  - リフレッシュトークン: HTTPOnly Cookie（本番）

encryption:
  - 通信: TLS 1.3
  - データベース: SQLite暗号化（オプション）
```

---

# 12. テスト戦略

## 12.1 テストピラミッド

```
        /\
       /  \      E2E テスト（5%）
      /    \     - Playwright
     /------\
    /        \   統合テスト（25%）
   /          \  - API テスト (pytest)
  /------------\
 /              \ ユニットテスト（70%）
/                \ - Backend: pytest
------------------\ - Frontend: Vitest + React Testing Library
```

## 12.2 テスト種別

| 種別 | ツール | 対象 |
|------|--------|------|
| ユニットテスト | pytest, Vitest | 個別関数、コンポーネント |
| 統合テスト | pytest + httpx | APIエンドポイント |
| E2Eテスト | Playwright | ユーザーシナリオ |
| 性能テスト | Locust | 同時接続、レスポンス時間 |

## 12.3 テストカバレッジ目標

```yaml
coverage_targets:
  backend:
    overall: 80%
    services: 90%
    routes: 85%
    models: 75%

  frontend:
    overall: 70%
    components: 80%
    hooks: 85%
    stores: 90%
```

## 12.4 重点テスト項目

| 機能 | テスト項目 |
|------|------------|
| 順位計算 | 勝点計算、得失点差、同率処理、直接対決 |
| 日程生成 | 除外ペア反映、時間割当、会場割当 |
| 認証 | ログイン/ログアウト、トークン更新、権限チェック |
| オフライン | データ保存、同期、競合解決 |
| 楽観的ロック | バージョン競合検出、解決フロー |

---

# 13. 運用・監視要件

## 13.1 監視項目

| カテゴリ | メトリクス | 閾値 |
|----------|-----------|------|
| 可用性 | Uptime | 99.5% |
| パフォーマンス | API レスポンス時間 | p95 < 500ms |
| パフォーマンス | ページロード時間 | < 3秒 |
| エラー | 5xx エラー率 | < 1% |
| リソース | CPU使用率 | < 80% |
| リソース | メモリ使用率 | < 85% |
| データベース | クエリ実行時間 | p95 < 100ms |

## 13.2 アラート設定

```yaml
alerts:
  critical:
    - サーバーダウン
    - データベース接続エラー
    - 認証システム障害

  warning:
    - API レスポンス遅延（> 1秒）
    - エラー率上昇（> 5%）
    - ディスク使用率（> 80%）

  info:
    - 新規ユーザー登録
    - 大会作成
    - 日次バックアップ完了
```

## 13.3 ログ設計

```yaml
log_levels:
  ERROR: 例外、障害
  WARNING: 非推奨使用、閾値超過
  INFO: 重要な業務イベント
  DEBUG: 開発時の詳細情報

log_format:
  timestamp: ISO 8601
  level: ERROR/WARNING/INFO/DEBUG
  service: backend/frontend
  correlation_id: リクエスト追跡用UUID
  message: ログメッセージ
  context: 追加情報（JSON）

log_retention:
  production: 90日
  staging: 30日
  development: 7日
```

## 13.4 ヘルスチェック

```yaml
endpoints:
  /health:
    description: 基本的な生存確認
    response: { status: "ok" }

  /health/ready:
    description: サービス準備完了確認
    checks:
      - database_connection
      - cache_connection
    response: { status: "ready", checks: {...} }

  /health/live:
    description: Kubernetes Liveness Probe用
    response: { status: "alive" }
```

---

# 14. バックアップ・リカバリ

## 14.1 バックアップ戦略

| 種別 | 頻度 | 保持期間 | 方式 |
|------|------|----------|------|
| 日次フルバックアップ | 毎日 02:00 | 30日 | SQLite ファイルコピー |
| 大会終了時バックアップ | イベント駆動 | 無期限 | 完全スナップショット |
| 設定バックアップ | 変更時 | 90日 | Git管理 |

## 14.2 バックアップ手順

```bash
# 自動バックアップスクリプト
#!/bin/bash

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_FILE="/data/urawa_cup.db"

# SQLiteバックアップ
sqlite3 $DB_FILE ".backup '${BACKUP_DIR}/urawa_cup_${TIMESTAMP}.db'"

# 圧縮
gzip ${BACKUP_DIR}/urawa_cup_${TIMESTAMP}.db

# 古いバックアップ削除（30日以上）
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

# 完了通知
echo "Backup completed: urawa_cup_${TIMESTAMP}.db.gz"
```

## 14.3 リカバリ手順

```yaml
recovery_procedures:
  point_in_time_recovery:
    rto: 1時間
    rpo: 24時間
    steps:
      1. サービス停止
      2. 最新バックアップ特定
      3. バックアップ復元
      4. 整合性チェック
      5. サービス再開
      6. 動作確認

  disaster_recovery:
    rto: 4時間
    rpo: 24時間
    steps:
      1. 代替環境準備
      2. バックアップ転送
      3. 環境構築
      4. データ復元
      5. DNS切り替え
      6. 動作確認
```

## 14.4 データエクスポート

```yaml
export_formats:
  - JSON: 完全データエクスポート
  - CSV: チーム・選手・試合結果
  - Excel: 報告書形式

export_schedule:
  - 大会終了後: 自動エクスポート
  - 手動: 管理画面から随時実行可能

data_portability:
  - 他システムへの移行サポート
  - 標準フォーマット（JSON Schema定義）
```

---

# 15. 国際化対応（将来拡張）

## 15.1 対応言語（予定）

| 言語 | コード | 優先度 |
|------|--------|--------|
| 日本語 | ja | 現在対応 |
| 英語 | en | Phase 2 |
| 中国語（簡体） | zh-CN | Phase 3 |
| 韓国語 | ko | Phase 3 |

## 15.2 i18n設計

```typescript
// i18n設定例
const resources = {
  ja: {
    translation: {
      match: {
        score: "スコア",
        homeTeam: "ホーム",
        awayTeam: "アウェイ",
        status: {
          scheduled: "予定",
          completed: "終了",
          cancelled: "中止"
        }
      }
    }
  },
  en: {
    translation: {
      match: {
        score: "Score",
        homeTeam: "Home",
        awayTeam: "Away",
        status: {
          scheduled: "Scheduled",
          completed: "Completed",
          cancelled: "Cancelled"
        }
      }
    }
  }
};
```

## 15.3 ローカライズ対象

```yaml
localization_scope:
  - UI テキスト
  - エラーメッセージ
  - 日付・時刻フォーマット
  - 数値フォーマット
  - 報告書テンプレート

excluded:
  - チーム名（ユーザー入力）
  - 選手名（ユーザー入力）
  - 大会名（ユーザー入力）
```
