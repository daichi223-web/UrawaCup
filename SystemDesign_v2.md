# 浦和カップ システム設計 - 問題分析と解決策

## 1. 予見される問題と解決策

### 1.1 アーキテクチャ上の問題

| 問題 | 原因 | 影響 | 解決策 |
|------|------|------|--------|
| **HTTPクライアントの乱立** | 各機能で個別にfetch/axiosを使用 | 認証・エラー処理の重複、不整合 | シングルトンHTTPクライアント |
| **命名規則の不一致** | バックエンド(snake_case)とフロントエンド(camelCase)の混在 | 型エラー、バグの温床 | 自動変換インターセプター |
| **型定義の重複** | 手動で型定義を作成 | バックエンドとの乖離 | OpenAPIから自動生成 |
| **エラー形式のバラつき** | 各APIで異なるエラー形式 | エラーハンドリングの複雑化 | 統一エラー形式の正規化 |
| **認証状態の分散管理** | ローカルストレージ直接参照 | セキュリティ問題、状態の不整合 | AuthManager一元管理 |

### 1.2 データ整合性の問題

```mermaid
flowchart TD
    subgraph 問題シナリオ
        A[会場Aで結果入力] --> B[同時に会場Bで入力]
        B --> C{順位計算が競合}
        C --> D[不整合な順位表]
    end
    
    subgraph 解決策
        E[楽観的ロック] --> F[バージョン番号チェック]
        F --> G[競合時は再取得]
        G --> H[整合性保証]
    end
```

| 問題 | シナリオ | 解決策 |
|------|----------|--------|
| **同時編集による競合** | 複数会場から同時に結果入力 | 楽観的ロック（version列） |
| **オフライン時のデータ損失** | ネット切断中に入力したデータ消失 | ローカルQueue + 同期 |
| **順位計算のタイミング** | 入力中に順位が変動 | トランザクション + 計算ロック |
| **得点者名の不一致** | 同一選手が異なる名前で登録 | player_idによる正規化 |

### 1.3 オフライン対応の問題

```mermaid
sequenceDiagram
    participant U as ユーザー
    participant App as アプリ
    participant Queue as SyncQueue
    participant API as サーバー
    
    Note over U,API: オフライン状態
    
    U->>App: 試合結果入力
    App->>App: バリデーション
    App->>Queue: キューに追加
    Queue-->>App: pendingId返却
    App-->>U: 保存完了（仮）
    
    Note over U,API: オンライン復帰
    
    Queue->>API: 順次送信
    
    alt 成功
        API-->>Queue: 200 OK
        Queue->>Queue: キューから削除
        Queue-->>App: 同期完了通知
    else 競合
        API-->>Queue: 409 Conflict
        Queue-->>App: 競合通知
        App-->>U: 競合解決ダイアログ
    end
```

---

## 2. プロジェクト規約（project-conventions.yml）

```yaml
# project-conventions.yml - 浦和カップ トーナメント管理システム

project:
  name: "urawa-cup-tournament"
  type: "web-app"
  description: "浦和カップ高校サッカー大会管理システム"

# ===== 命名規則 =====
naming:
  api:
    request_body: "snake_case"      # FastAPIに合わせる
    response_body: "snake_case"     # FastAPIに合わせる
    url_path: "kebab-case"          # /api/v1/match-results
    query_params: "snake_case"      # ?team_id=1
  
  code:
    variables: "camelCase"          # const matchResult
    constants: "UPPER_SNAKE_CASE"   # const MAX_TEAMS = 24
    functions: "camelCase"          # function calculateStandings()
    classes: "PascalCase"           # class MatchService
    interfaces: "PascalCase"        # interface Match
    types: "PascalCase"             # type MatchStatus
    enums: "PascalCase"             # enum MatchStage
  
  files:
    components: "PascalCase.tsx"    # MatchCard.tsx
    hooks: "use*.ts"                # useMatches.ts
    services: "*.service.ts"        # match.service.ts
    types: "*.types.ts"             # match.types.ts
    tests: "*.test.ts"              # match.test.ts

# ===== アーキテクチャ =====
architecture:
  http_client:
    count: 1                         # 必ず1つのみ
    library: "axios"
    base_location: "src/core/http"
  
  state_management:
    library: "zustand"
    location: "src/core/store"
  
  authentication:
    type: "jwt"
    token_storage: "memory"          # XSS対策でメモリ保持
    refresh_strategy: "silent"
    manager_location: "src/core/auth"
  
  error_handling:
    format: "{ code, message, status, details }"
    location: "src/core/errors"
  
  offline:
    enabled: true
    storage: "IndexedDB"
    sync_queue: "src/core/sync"

# ===== 型定義 =====
types:
  generation: "auto"
  source: "openapi"
  endpoint: "http://localhost:8000/openapi.json"
  output_location: "src/api/generated"

# ===== ディレクトリ構成 =====
structure:
  pattern: "feature-based"
```

---

## 3. 改訂版ディレクトリ構成

```
src/
├── core/                           # 基盤（変更頻度：低）
│   ├── http/
│   │   ├── client.ts               # シングルトンHTTPクライアント
│   │   ├── interceptors/
│   │   │   ├── auth.ts             # 認証ヘッダー付与
│   │   │   ├── error.ts            # エラー正規化
│   │   │   └── transform.ts        # snake_case ↔ camelCase変換
│   │   └── index.ts
│   │
│   ├── auth/
│   │   ├── manager.ts              # AuthManager（シングルトン）
│   │   ├── store.ts                # Zustand認証ストア
│   │   └── index.ts
│   │
│   ├── errors/
│   │   ├── types.ts                # AppError型定義
│   │   ├── handler.ts              # グローバルエラーハンドラ
│   │   └── index.ts
│   │
│   ├── sync/                       # オフライン同期
│   │   ├── queue.ts                # SyncQueue
│   │   ├── storage.ts              # IndexedDB操作
│   │   ├── conflict.ts             # 競合解決
│   │   └── index.ts
│   │
│   └── config/
│       └── index.ts                # 環境設定
│
├── features/                       # 機能別（変更頻度：高）
│   ├── tournaments/                # 大会管理
│   │   ├── api.ts
│   │   ├── hooks.ts
│   │   ├── components/
│   │   ├── types.ts
│   │   └── index.ts
│   │
│   ├── teams/                      # チーム管理
│   │   ├── api.ts
│   │   ├── hooks.ts
│   │   ├── components/
│   │   ├── types.ts
│   │   └── index.ts
│   │
│   ├── players/                    # 選手管理
│   │   ├── api.ts
│   │   ├── hooks.ts
│   │   ├── components/
│   │   │   └── PlayerSuggest.tsx   # サジェストUI
│   │   ├── types.ts
│   │   └── index.ts
│   │
│   ├── matches/                    # 試合管理
│   │   ├── api.ts
│   │   ├── hooks.ts
│   │   ├── components/
│   │   │   ├── MatchCard.tsx
│   │   │   ├── ScoreInput.tsx
│   │   │   └── GoalInput.tsx
│   │   ├── types.ts
│   │   └── index.ts
│   │
│   ├── standings/                  # 順位表
│   │   ├── api.ts
│   │   ├── hooks.ts
│   │   ├── components/
│   │   │   └── StandingsTable.tsx
│   │   ├── calculator.ts           # 順位計算ロジック
│   │   ├── types.ts
│   │   └── index.ts
│   │
│   ├── exclusions/                 # 対戦除外設定
│   │   ├── api.ts
│   │   ├── hooks.ts
│   │   ├── components/
│   │   │   └── ExclusionMatrix.tsx
│   │   ├── types.ts
│   │   └── index.ts
│   │
│   └── reports/                    # 報告書
│       ├── api.ts
│       ├── hooks.ts
│       ├── components/
│       ├── types.ts
│       └── index.ts
│
├── shared/                         # 共有
│   ├── components/
│   │   ├── Layout/
│   │   ├── Button/
│   │   ├── Modal/
│   │   ├── Toast/
│   │   └── OfflineIndicator.tsx
│   │
│   ├── hooks/
│   │   ├── useOnlineStatus.ts
│   │   ├── useWebSocket.ts
│   │   └── useSyncStatus.ts
│   │
│   └── utils/
│       ├── date.ts
│       └── format.ts
│
├── api/
│   ├── generated/                  # OpenAPIから自動生成
│   │   └── schema.ts
│   └── client.ts
│
└── pages/                          # ページコンポーネント
    ├── Dashboard.tsx
    ├── Teams.tsx
    ├── Schedule.tsx
    ├── Results.tsx
    ├── Standings.tsx
    └── Reports.tsx
```

---

## 4. 改訂版データベース設計

### 4.1 楽観的ロック対応のER図

```mermaid
erDiagram
    tournaments ||--o{ groups : has
    tournaments ||--o{ venues : has
    tournaments ||--o{ report_recipients : has
    
    groups ||--o{ teams : contains
    groups ||--o{ matches : has
    groups ||--o{ exclusion_pairs : has
    
    teams ||--o{ players : has
    teams ||--o{ standings : has
    
    matches ||--o{ goals : has
    matches ||--o{ match_locks : has
    
    sync_queue ||--o{ sync_queue_items : has

    tournaments {
        int id PK
        string name
        int edition
        date start_date
        date end_date
        int match_duration
        int interval_minutes
        int version "楽観的ロック用"
        datetime created_at
        datetime updated_at
    }
    
    teams {
        int id PK
        int tournament_id FK
        string name
        string short_name
        enum team_type "local/invited"
        boolean is_venue_host
        string group_id
        int group_order
        string prefecture
        int version "楽観的ロック用"
    }
    
    players {
        int id PK
        int team_id FK
        int number
        string name
        string name_kana
        string name_normalized "検索用正規化名"
    }
    
    matches {
        int id PK
        int tournament_id FK
        string group_id
        int venue_id FK
        int home_team_id FK
        int away_team_id FK
        date match_date
        time match_time
        int match_order
        enum stage
        enum status
        int home_score_half1
        int home_score_half2
        int home_score_total
        int away_score_half1
        int away_score_half2
        int away_score_total
        int home_pk
        int away_pk
        boolean has_penalty_shootout
        int version "楽観的ロック用"
        datetime updated_at
    }
    
    match_locks {
        int id PK
        int match_id FK "UNIQUE"
        int user_id FK
        datetime locked_at
        datetime expires_at "5分後自動解除"
    }
    
    goals {
        int id PK
        int match_id FK
        int team_id FK
        int player_id FK "NULL可"
        string scorer_name "自由入力用"
        int minute
        int half
        int version
    }
    
    standings {
        int id PK
        int tournament_id FK
        string group_id
        int team_id FK
        int rank
        int played
        int won
        int drawn
        int lost
        int goals_for
        int goals_against
        int goal_difference
        int points
        int version
        datetime calculated_at
    }
    
    exclusion_pairs {
        int id PK
        int tournament_id FK
        string group_id
        int team1_id FK
        int team2_id FK
        string reason
    }
    
    sync_queue {
        int id PK
        string client_id "デバイス識別"
        datetime created_at
    }
    
    sync_queue_items {
        int id PK
        int queue_id FK
        string entity_type "match/goal"
        int entity_id
        string operation "create/update/delete"
        json payload
        enum status "pending/synced/conflict"
        datetime created_at
        datetime synced_at
    }
```

### 4.2 主要テーブルの詳細定義

#### matches（試合）- 楽観的ロック対応

```sql
CREATE TABLE matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id),
    group_id VARCHAR(1),
    venue_id INTEGER REFERENCES venues(id),
    home_team_id INTEGER NOT NULL REFERENCES teams(id),
    away_team_id INTEGER NOT NULL REFERENCES teams(id),
    match_date DATE NOT NULL,
    match_time TIME NOT NULL,
    match_order INTEGER NOT NULL,
    stage VARCHAR(20) NOT NULL DEFAULT 'preliminary',
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    
    -- スコア
    home_score_half1 INTEGER,
    home_score_half2 INTEGER,
    home_score_total INTEGER,
    away_score_half1 INTEGER,
    away_score_half2 INTEGER,
    away_score_total INTEGER,
    home_pk INTEGER,
    away_pk INTEGER,
    has_penalty_shootout BOOLEAN DEFAULT FALSE,
    
    -- 楽観的ロック
    version INTEGER NOT NULL DEFAULT 1,
    
    -- メタデータ
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tournament_id, match_date, venue_id, match_order)
);

-- バージョン自動更新トリガー
CREATE TRIGGER update_match_version
AFTER UPDATE ON matches
BEGIN
    UPDATE matches 
    SET version = version + 1, updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
```

#### match_locks（排他ロック）

```sql
CREATE TABLE match_locks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL UNIQUE REFERENCES matches(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    locked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    
    -- 5分後に自動期限切れ
    CHECK (expires_at > locked_at)
);

-- 期限切れロックを自動削除するジョブを別途実装
```

#### sync_queue_items（オフライン同期キュー）

```sql
CREATE TABLE sync_queue_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id VARCHAR(36) NOT NULL,  -- UUID
    entity_type VARCHAR(50) NOT NULL,  -- 'match', 'goal'
    entity_id INTEGER,
    operation VARCHAR(20) NOT NULL,  -- 'create', 'update', 'delete'
    payload JSON NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'synced', 'conflict'
    error_message TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    synced_at DATETIME,
    
    INDEX idx_status (status),
    INDEX idx_client (client_id)
);
```

### 4.3 インデックス戦略

```sql
-- 頻繁なクエリ用インデックス
CREATE INDEX idx_matches_tournament_date ON matches(tournament_id, match_date);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_venue ON matches(venue_id, match_date);

CREATE INDEX idx_standings_tournament_group ON standings(tournament_id, group_id);
CREATE INDEX idx_standings_rank ON standings(tournament_id, group_id, rank);

CREATE INDEX idx_goals_match ON goals(match_id);
CREATE INDEX idx_goals_team ON goals(team_id);

CREATE INDEX idx_players_team ON players(team_id);
CREATE INDEX idx_players_name ON players(name_normalized);  -- サジェスト用

CREATE INDEX idx_exclusions_group ON exclusion_pairs(tournament_id, group_id);
```

---

## 5. 改訂版シーケンス図

### 5.1 試合結果入力（楽観的ロック対応）

```mermaid
sequenceDiagram
    participant U as 会場担当者
    participant F as フロントエンド
    participant L as ローカルStorage
    participant API as バックエンド
    participant DB as Database
    participant WS as WebSocket
    
    U->>F: 試合選択
    F->>API: GET /api/matches/{id}
    API->>DB: SELECT * FROM matches WHERE id = ?
    DB-->>API: match (version: 3)
    API-->>F: { ...match, version: 3 }
    F->>F: currentVersion = 3
    
    F->>API: POST /api/matches/{id}/lock
    API->>DB: INSERT INTO match_locks
    
    alt ロック成功
        DB-->>API: OK
        API-->>F: { lockId, expiresAt }
        F->>F: 入力フォーム表示
    else 既にロック中
        API-->>F: 409 Conflict { lockedBy, expiresAt }
        F-->>U: "○○さんが編集中（残り3分）"
    end
    
    U->>F: スコア入力
    U->>F: 得点者入力
    F->>API: GET /api/players/suggest?team_id=1&q=山
    API-->>F: [{ id: 1, name: "山田太郎" }, ...]
    U->>F: 選手選択
    
    U->>F: 保存ボタン
    F->>F: payload = { ...data, version: 3 }
    
    alt オンライン
        F->>API: PUT /api/matches/{id}/score
        Note over API: Content: { score, goals, version: 3 }
        
        API->>DB: BEGIN TRANSACTION
        API->>DB: SELECT version FROM matches WHERE id = ?
        DB-->>API: version: 3
        
        alt バージョン一致
            API->>DB: UPDATE matches SET ... WHERE id = ? AND version = 3
            API->>DB: INSERT INTO goals ...
            API->>DB: CALL recalculate_standings(?)
            API->>DB: COMMIT
            DB-->>API: OK
            API-->>F: 200 { ...match, version: 4 }
            
            API->>WS: broadcast("match_updated", matchId)
            F->>API: DELETE /api/matches/{id}/lock
            F-->>U: 保存完了
            
        else バージョン不一致（他者が更新済み）
            API->>DB: ROLLBACK
            API-->>F: 409 Conflict { currentVersion: 4, currentData }
            F-->>U: 競合ダイアログ表示
            U->>F: 上書き or 再読込 選択
        end
        
    else オフライン
        F->>L: SyncQueue.add({ type: 'update', data, version: 3 })
        L-->>F: queueId: "abc123"
        F-->>U: オフライン保存完了（同期待ち）
        F->>F: 画面に「未同期」バッジ表示
    end
```

### 5.2 オフライン同期処理

```mermaid
sequenceDiagram
    participant SW as ServiceWorker
    participant F as フロントエンド
    participant IDB as IndexedDB
    participant Q as SyncQueue
    participant API as バックエンド
    participant DB as Database
    
    Note over SW,DB: オンライン復帰検知
    
    SW->>SW: navigator.onLine = true
    SW->>F: CustomEvent("online")
    
    F->>Q: getpendingItems()
    Q->>IDB: SELECT * FROM sync_queue WHERE status = 'pending'
    IDB-->>Q: [item1, item2, item3]
    Q-->>F: pendingItems
    
    F->>F: 同期中インジケータ表示
    
    loop 各未同期アイテム
        F->>Q: processItem(item)
        
        alt item.operation == 'update'
            Q->>API: PUT /api/{entity}/{id}
            Note over Q,API: { payload, version: item.version }
            
            alt 成功
                API->>DB: UPDATE ... WHERE version = ?
                DB-->>API: rowsAffected: 1
                API-->>Q: 200 OK { newVersion }
                Q->>IDB: UPDATE sync_queue SET status = 'synced'
                
            else バージョン競合
                API-->>Q: 409 Conflict { serverData }
                Q->>IDB: UPDATE sync_queue SET status = 'conflict'
                Q-->>F: conflictItem
                F-->>F: 競合リストに追加
                
            else サーバーエラー
                API-->>Q: 500 Error
                Q->>Q: リトライキューに追加
            end
        end
    end
    
    F->>F: 同期完了チェック
    
    alt 競合あり
        F-->>F: 競合解決ダイアログ表示
        Note over F: ユーザーに選択させる
        F->>F: "サーバーの値を使う" or "自分の値で上書き"
    else 全て成功
        F->>F: "同期完了" トースト表示
    end
```

### 5.3 順位計算（トランザクション保証）

```mermaid
sequenceDiagram
    participant API as バックエンド
    participant DB as Database
    participant Cache as Redis/Memory
    participant WS as WebSocket
    
    Note over API: 試合結果保存トリガー
    
    API->>DB: BEGIN TRANSACTION
    
    API->>DB: UPDATE matches SET score = ... WHERE id = ?
    DB-->>API: OK
    
    API->>DB: SELECT * FROM matches<br/>WHERE tournament_id = ? AND group_id = ?<br/>AND status = 'completed'
    DB-->>API: 完了済み試合一覧
    
    API->>API: 順位計算ロジック実行
    Note over API: 1. 勝点計算<br/>2. 得失点差<br/>3. 総得点<br/>4. 直接対決
    
    API->>DB: DELETE FROM standings<br/>WHERE tournament_id = ? AND group_id = ?
    API->>DB: INSERT INTO standings VALUES ...
    
    API->>DB: COMMIT
    DB-->>API: OK
    
    API->>Cache: SET standings:{tournament}:{group} = [...]
    API->>Cache: EXPIRE standings:{tournament}:{group} 60
    
    API->>WS: broadcast("standings_updated", { tournamentId, groupId })
    
    par 全クライアントに配信
        WS-->>WS: Client A
        WS-->>WS: Client B
        WS-->>WS: Client C
    end
```

### 5.4 得点者入力（サジェスト付き）

```mermaid
sequenceDiagram
    participant U as ユーザー
    participant F as フロントエンド
    participant D as Debounce
    participant API as バックエンド
    participant DB as Database
    
    U->>F: 得点者入力欄にフォーカス
    F->>F: チームの選手キャッシュ確認
    
    alt キャッシュあり
        F->>F: キャッシュから候補表示
    else キャッシュなし
        F->>API: GET /api/teams/{teamId}/players
        API->>DB: SELECT * FROM players WHERE team_id = ?
        DB-->>API: 選手リスト
        API-->>F: players[]
        F->>F: キャッシュに保存
    end
    
    U->>F: "やま" と入力
    F->>D: debounce(300ms)
    D->>F: 実行
    
    F->>F: ローカルフィルタリング
    Note over F: players.filter(p =><br/>  p.name.includes("やま") ||<br/>  p.nameKana.includes("やま")<br/>)
    
    F-->>F: サジェスト表示<br/>["山田太郎", "山本次郎"]
    
    alt 候補から選択
        U->>F: "山田太郎" クリック
        F->>F: { playerId: 1, scorerName: "山田太郎" }
    else 自由入力
        U->>F: "山田（控え）" と入力してEnter
        F->>F: { playerId: null, scorerName: "山田（控え）" }
    end
    
    F->>F: 得点リストに追加
```

### 5.5 報告書生成（非同期処理）

```mermaid
sequenceDiagram
    participant U as 管理者
    participant F as フロントエンド
    participant API as バックエンド
    participant DB as Database
    participant PDF as PDF生成
    participant S3 as ファイル保存
    
    U->>F: 報告書出力ボタン
    F->>F: 出力条件ダイアログ
    Note over F: 日付: 2024-03-29<br/>会場: 浦和南高G<br/>形式: PDF
    
    U->>F: 生成開始
    F->>API: POST /api/reports/generate
    Note over F,API: { date, venueId, format: "pdf" }
    
    API-->>F: 202 Accepted { jobId: "xyz789" }
    F->>F: 進捗表示開始
    
    API->>DB: INSERT INTO report_jobs (id, status)
    
    par 非同期処理
        API->>DB: SELECT matches WHERE date = ? AND venue_id = ?
        DB-->>API: matches[]
        
        API->>DB: SELECT goals WHERE match_id IN (...)
        DB-->>API: goals[]
        
        API->>DB: SELECT recipient FROM report_recipients
        DB-->>API: recipients[]
        
        API->>PDF: generateReport(matches, goals, recipients)
        Note over PDF: ヘッダー生成<br/>試合結果テーブル<br/>得点経過
        PDF-->>API: pdfBuffer
        
        API->>S3: upload(pdfBuffer)
        S3-->>API: fileUrl
        
        API->>DB: UPDATE report_jobs SET status = 'completed', url = ?
    end
    
    loop ポーリング（3秒間隔）
        F->>API: GET /api/reports/jobs/{jobId}
        API->>DB: SELECT status, url FROM report_jobs
        DB-->>API: { status, url }
        API-->>F: { status: "processing", progress: 60 }
    end
    
    API-->>F: { status: "completed", url: "..." }
    F->>F: ダウンロードリンク表示
    U->>F: ダウンロード
    F->>S3: GET file
    S3-->>F: PDF file
```

### 5.6 WebSocketリアルタイム更新

```mermaid
sequenceDiagram
    participant A as 会場A
    participant B as 会場B
    participant V as 閲覧者
    participant WS as WebSocketサーバー
    participant API as バックエンド
    participant Redis as Pub/Sub
    
    Note over A,Redis: 接続確立
    
    A->>WS: connect(token)
    WS->>WS: 認証検証
    WS->>Redis: SUBSCRIBE updates:tournament:1
    WS-->>A: connected
    
    B->>WS: connect(token)
    WS->>Redis: SUBSCRIBE updates:tournament:1
    WS-->>B: connected
    
    V->>WS: connect (認証なし = 閲覧のみ)
    WS->>Redis: SUBSCRIBE updates:tournament:1
    WS-->>V: connected (readonly)
    
    Note over A,Redis: 会場Aで結果入力
    
    A->>API: PUT /api/matches/1/score
    API->>API: 保存 & 順位計算
    API->>Redis: PUBLISH updates:tournament:1 "match_updated:1"
    
    Redis-->>WS: message
    
    par 全クライアントに配信
        WS-->>A: { type: "match_updated", matchId: 1 }
        WS-->>B: { type: "match_updated", matchId: 1 }
        WS-->>V: { type: "match_updated", matchId: 1 }
    end
    
    A->>A: 自分の更新 → 無視
    B->>API: GET /api/matches/1
    B->>B: 画面更新
    V->>API: GET /api/matches/1
    V->>V: 画面更新
    
    Note over A,Redis: 順位表更新
    
    API->>Redis: PUBLISH updates:tournament:1 "standings_updated:A"
    
    par 配信
        WS-->>A: { type: "standings_updated", groupId: "A" }
        WS-->>B: { type: "standings_updated", groupId: "A" }
        WS-->>V: { type: "standings_updated", groupId: "A" }
    end
```

---

## 6. エラーハンドリング設計

### 6.1 統一エラー形式

```typescript
// src/core/errors/types.ts

export type ErrorCode =
  | 'BAD_REQUEST'
  | 'UNAUTHORIZED'
  | 'FORBIDDEN'
  | 'NOT_FOUND'
  | 'CONFLICT'
  | 'VALIDATION_ERROR'
  | 'VERSION_CONFLICT'
  | 'LOCK_CONFLICT'
  | 'OFFLINE'
  | 'SYNC_ERROR'
  | 'SERVER_ERROR'
  | 'UNKNOWN';

export interface AppError {
  code: ErrorCode;
  message: string;
  status?: number;
  details?: {
    field?: string;
    expected?: unknown;
    actual?: unknown;
    conflictData?: unknown;
  };
  retryable: boolean;
}
```

### 6.2 エラー別対処フロー

```mermaid
flowchart TD
    A[APIエラー発生] --> B{エラーコード判定}
    
    B -->|UNAUTHORIZED| C[ログイン画面へ]
    B -->|FORBIDDEN| D[権限エラー表示]
    B -->|NOT_FOUND| E[404ページ or トースト]
    
    B -->|VERSION_CONFLICT| F[競合解決フロー]
    F --> F1{ユーザー選択}
    F1 -->|サーバー優先| F2[データ再取得]
    F1 -->|自分の値で上書き| F3[強制更新API]
    
    B -->|LOCK_CONFLICT| G[ロック待機フロー]
    G --> G1[残り時間表示]
    G1 --> G2{タイムアウト?}
    G2 -->|Yes| G3[ロック強制解除]
    G2 -->|No| G4[定期的に再試行]
    
    B -->|OFFLINE| H[オフライン処理]
    H --> H1[ローカル保存]
    H1 --> H2[同期キュー追加]
    
    B -->|VALIDATION_ERROR| I[フィールドエラー表示]
    B -->|SERVER_ERROR| J[リトライ or エラー画面]
```

---

## 7. 設計原則チェックリスト

### 浦和カップシステムでの適用状況

| 原則 | 適用 | 実装方法 |
|------|------|----------|
| **Single Source of Truth** | ✅ | HTTPクライアント1つ、AuthManager1つ |
| **Contract First** | ✅ | OpenAPIスキーマから型自動生成 |
| **Explicit Dependencies** | ✅ | DI/Factory経由でのみ依存注入 |
| **Optimistic Locking** | ✅ | version列で競合検知 |
| **Offline First** | ✅ | SyncQueue + IndexedDB |
| **Consistent Naming** | ✅ | インターセプターで自動変換 |
| **Normalized Errors** | ✅ | AppError統一形式 |

### 開発前チェックリスト

```
□ project-conventions.yml を作成したか？
□ HTTPクライアントは1つのみか？
□ 型はOpenAPIから自動生成しているか？
□ 認証トークンの管理は1箇所か？
□ エラー形式は統一されているか？
□ 命名規則変換は自動化されているか？
□ オフライン対応の設計は完了しているか？
□ 楽観的ロックの設計は完了しているか？
□ WebSocket接続の設計は完了しているか？
```
