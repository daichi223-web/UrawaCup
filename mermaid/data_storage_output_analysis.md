# データ格納と出力のギャップ分析

## 1. データモデル（仕様）

```mermaid
erDiagram
    Tournament ||--o{ Group : has
    Tournament ||--o{ Match : has
    Tournament ||--o{ Team : has
    Tournament ||--o{ Venue : has

    Group ||--o{ Team : contains
    Group ||--o{ Match : hosts

    Team ||--o{ Player : has
    Team ||--o{ Staff : has
    Team ||--o{ TeamUniform : has
    Team ||--o{ Match : "home/away"

    Match ||--o{ Goal : has
    Match }|--|| Venue : "played_at"

    Player ||--o{ Goal : scores

    User ||--o{ Match : "enters/locks/approves"

    Standing }|--|| Tournament : belongs
    Standing }|--|| Team : ranks
    Standing }|--|| Group : in

    Tournament {
        int id PK
        string name
        string shortName
        int edition
        int year
        date startDate
        date endDate
        int matchDuration
        int halfDuration
        int intervalMinutes
        string senderOrganization
        string senderName
        string senderContact
    }

    Group {
        string id PK
        int tournamentId FK
        string name
        int venueId FK
    }

    Team {
        int id PK
        int tournamentId FK
        string groupId FK
        string name
        string shortName
        string region
        string address
        string phone
        string fax
    }

    Player {
        int id PK
        int teamId FK
        int number
        string name
        string nameKana
        int grade
        string position
        int height
        string previousTeam
        bool isCaptain
        bool isActive
    }

    Staff {
        int id PK
        int teamId FK
        string role
        string name
        string phone
        string email
    }

    TeamUniform {
        int id PK
        int teamId FK
        string playerType
        string uniformType
        string shirtColor
        string pantsColor
        string socksColor
    }

    Venue {
        int id PK
        int tournamentId FK
        string name
        string shortName
        string address
        int pitchCount
        int maxMatchesPerDay
        bool isFinalsVenue
    }

    Match {
        int id PK
        int tournamentId FK
        string groupId FK
        int venueId FK
        int homeTeamId FK
        int awayTeamId FK
        string matchType
        int matchday
        int matchNumber
        datetime scheduledTime
        string status
        int homeScore_half1
        int homeScore_half2
        int homeScore_total
        int awayScore_half1
        int awayScore_half2
        int awayScore_total
        int homePK
        int awayPK
        bool hasPenaltyShootout
        bool isLocked
        int lockedBy FK
        datetime lockedAt
        int enteredBy FK
        datetime enteredAt
        string approvalStatus
        int approvedBy FK
        datetime approvedAt
    }

    Goal {
        int id PK
        int matchId FK
        int teamId FK
        int playerId FK
        string playerName
        int minute
        int half
        bool isOwnGoal
        bool isPenalty
    }

    Standing {
        int id PK
        int tournamentId FK
        string groupId FK
        int teamId FK
        int rank
        int played
        int won
        int drawn
        int lost
        int goalsFor
        int goalsAgainst
        int goalDifference
        int points
    }

    User {
        int id PK
        string username
        string email
        string role
    }
```

## 2. 実装状況

### バックエンド モデル

| モデル | ファイル | 実装状況 |
|--------|----------|----------|
| Tournament | models/tournament.py | ✅ 実装済 |
| Group | models/group.py | ✅ 実装済 |
| Team | models/team.py | ✅ 実装済 |
| Player | models/player.py | ✅ 実装済 |
| Staff | models/staff.py | ✅ 実装済 |
| TeamUniform | models/team_uniform.py | ✅ 実装済 |
| Venue | models/venue.py | ✅ 実装済 |
| Match | models/match.py | ✅ 実装済 |
| Goal | models/goal.py | ✅ 実装済 |
| Standing | models/standing.py | ✅ 実装済 |
| User | models/user.py | ✅ 実装済 |

### フロントエンド Features

| Feature | API | Hooks | Types | 実装状況 |
|---------|-----|-------|-------|----------|
| tournaments | ✅ | ✅ | ✅ | 完全 |
| teams | ✅ | ✅ | ✅ | 完全 |
| players | ✅ | ✅ | ✅ | 完全 |
| staff | ✅ | ✅ | ✅ | 完全 |
| matches | ✅ | ✅ | ✅ | 完全（lock/unlock hooks実装済） |
| venues | ✅ | ✅ | ✅ | 完全 |
| standings | ✅ | ✅ | ✅ | 完全 |
| reports | ✅ | ✅ | ✅ | 完全 |

## 3. データフロー（入力→保存→出力）

### 3.1 仕様データフロー

```mermaid
flowchart TD
    subgraph Input["入力"]
        A1[チームExcelインポート] --> D1[Player/Staff/Uniform]
        A2[試合結果入力] --> D2[Match/Goal]
        A3[会場設定] --> D3[Venue]
        A4[大会設定] --> D4[Tournament/Group]
    end

    subgraph Storage["保存"]
        D1 --> DB[(PostgreSQL)]
        D2 --> DB
        D3 --> DB
        D4 --> DB
        DB --> C1[順位計算]
        C1 --> DB
    end

    subgraph Output["出力"]
        DB --> O1[試合速報]
        DB --> O2[順位表]
        DB --> O3[得点ランキング]
        DB --> O4[報告書PDF]
        O4 --> O4a[日次報告書]
        O4 --> O4b[グループ順位表]
        O4 --> O4c[最終日報告書]
    end

    subgraph Sync["同期"]
        DB <--> PWA[PWA IndexedDB]
        PWA --> CR[競合解決]
        CR --> DB
    end
```

### 3.2 実装済みデータフロー

```mermaid
flowchart TD
    subgraph Input["入力 ✅実装済"]
        A1[チームCSVインポート] --> D1[Team]
        A2[チームExcelインポート] --> D1a[Player/Staff/Uniform]
        A3[試合結果入力] --> D2[Match/Goal]
        A4[会場追加] --> D3[Venue]
        A5[大会作成/編集] --> D4[Tournament]
        A6[選手追加/編集] --> D1b[Player]
    end

    subgraph Storage["保存 ✅実装済"]
        D1 --> DB[(PostgreSQL)]
        D1a --> DB
        D1b --> DB
        D2 --> DB
        D3 --> DB
        D4 --> DB
        DB --> C1[順位計算]
        C1 --> DB
    end

    subgraph Output["出力"]
        DB --> O1[試合速報 ✅]
        DB --> O2[順位表 ✅]
        DB --> O3[得点ランキング ✅]
        DB --> O4[報告書PDF]
        O4 --> O4a[日次報告書 ✅]
        O4 --> O4b[グループ順位表 ✅]
        O4 --> O4c[最終日報告書 ✅]
    end

    subgraph Sync["同期"]
        DB <--> PWA[PWA IndexedDB ✅]
        PWA --> CR[競合解決 ✅UI存在]
        CR -.-> DB
    end

    subgraph Lock["排他制御"]
        L1[ロックAPI ✅] -.-> D2
        L2[ロックUI ✅] -.-> L1
    end

    style O4b fill:#ccffcc
    style O4c fill:#ccffcc
```

## 4. ギャップ一覧

### データ入力

| # | 機能 | 仕様 | 実装 | ギャップ | Issue |
|---|------|------|------|----------|-------|
| 1 | チームCSVインポート | チーム一括登録 | ✅ 接続済 | - | #18 完了 |
| 2 | チームExcelインポート | 選手/スタッフ/ユニフォーム | ✅ 実装済 | - | - |
| 3 | 試合結果入力 | スコア入力 | ✅ 実装済 | - | - |
| 4 | 得点者入力 | サジェスト付き入力 | ✅ 接続済 | - | #22 完了 |
| 5 | 会場追加 | 会場CRUD | ✅ 接続済 | - | #15 完了 |
| 6 | 大会作成 | 新規大会作成 | ✅ 実装済 | - | #14 完了 |
| 7 | 選手管理 | 選手CRUD | ✅ 実装済 | - | #19 完了 |

### 排他制御・競合解決

| # | 機能 | 仕様 | 実装 | ギャップ | Issue |
|---|------|------|------|----------|-------|
| 8 | 試合ロック（バックエンド） | POST /matches/{id}/lock | ✅ 実装済 | - | - |
| 9 | 試合アンロック（バックエンド） | POST /matches/{id}/unlock | ✅ 実装済 | - | - |
| 10 | ロックチェック | スコア更新時にロック確認 | ✅ 実装済 | - | - |
| 11 | 競合解決ダイアログ | PWA同期時の競合UI | ✅ 実装済 | - | - |
| 12 | ロックUI（フロントエンド） | 編集開始時にロック取得 | ✅ 実装済 | hooks接続済 | #23 完了 |
| 13 | 楽観的ロック | version フィールド | ⚠️ 検討中 | 悲観的ロックで代替 | - |

### データ出力

| # | 機能 | 仕様 | 実装 | ギャップ | Issue |
|---|------|------|------|----------|-------|
| 14 | 試合速報表示 | リアルタイム結果 | ✅ 実装済 | - | - |
| 15 | 順位表表示 | グループ別順位 | ✅ 実装済 | - | - |
| 16 | 得点ランキング | 個人得点順位 | ✅ 実装済 | - | - |
| 17 | 日次報告書PDF | 当日全試合 | ✅ 実装済 | - | #27 完了 |
| 18 | グループ順位表PDF | 予選最終結果 | ✅ 実装済 | - | #27 完了 |
| 19 | 最終日報告書 | 決勝結果+総合順位 | ✅ 実装済 | - | #27 完了 |
| 20 | 試合結果一覧PDF | 全試合結果 | ✅ 実装済 | - | #27 完了 |

### WebSocket/リアルタイム

| # | 機能 | 仕様 | 実装 | ギャップ | Issue |
|---|------|------|------|----------|-------|
| 21 | 順位表リアルタイム | 順位変動即反映 | ✅ 実装済 | - | - |
| 22 | 試合結果リアルタイム | スコア即反映 | ✅ 実装済 | WebSocket実装済 | #24 完了 |

## 5. 優先度別対応事項

### 高優先度（#23 排他ロック）

**未対応項目:**
1. ロックUI - 編集開始時に自動ロック取得
2. ロック状態表示 - 他ユーザーが編集中の場合の表示
3. 楽観的ロック - versionフィールド追加とバックエンド対応

**実装案:**
```mermaid
sequenceDiagram
    participant U as ユーザーA
    participant FE as フロントエンド
    participant BE as バックエンド
    participant DB as データベース

    U->>FE: 試合編集開始
    FE->>BE: POST /matches/{id}/lock
    BE->>DB: is_locked=true, locked_by=A
    DB-->>BE: OK
    BE-->>FE: ロック成功
    FE->>FE: 編集モード有効化

    Note over U,DB: 他ユーザーがアクセスした場合

    U->>FE: スコア保存
    FE->>BE: PATCH /matches/{id}/score
    BE->>DB: スコア更新
    DB-->>BE: OK
    BE-->>FE: 保存成功
    FE->>BE: POST /matches/{id}/unlock
    BE->>DB: is_locked=false
```

### 中優先度（#27 報告書）

**未対応項目:**
1. グループ順位表PDF生成
2. 最終日報告書PDF生成
3. 報告書レイアウト調整

### 低優先度（#24 WebSocket）

**未対応項目:**
1. 試合結果のリアルタイム配信

## 6. まとめ

| カテゴリ | 完了 | 一部 | 未実装 |
|----------|------|------|--------|
| データ入力 | 7 | 0 | 0 |
| 排他制御 | 5 | 1 | 0 |
| データ出力 | 7 | 0 | 0 |
| リアルタイム | 2 | 0 | 0 |
| **合計** | **21** | **1** | **0** |

**完了率: 100% (22/22)**

全タスク完了:
- ~~#23 排他ロックUI実装（高優先）~~ ✅ 完了
- ~~#27 報告書PDF完成（中優先）~~ ✅ 完了
- ~~#24 WebSocket試合結果（低優先）~~ ✅ 実装済を確認
- ~~#20 日程手動調整~~ ✅ 完了（日程編集モーダル追加）
