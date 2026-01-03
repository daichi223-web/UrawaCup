# UrawaCup データベース構造

**作成日**: 2026-01-01
**データベース**: SQLite (SQLAlchemy ORM)

---

## ER図（概念）

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Tournament │────<│    Group    │────<│    Team     │
│   (大会)    │     │  (グループ) │     │  (チーム)   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Venue    │────<│    Match    │────<│    Goal     │
│   (会場)    │     │   (試合)    │     │   (得点)    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  Standing   │     │   Player    │
                    │  (順位表)   │     │   (選手)    │
                    └─────────────┘     └─────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    User     │     │ ExclusionPair│    │ReportRecipient│
│ (ユーザー)  │     │ (除外ペア)   │    │ (送信先)    │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## テーブル一覧

| # | テーブル名 | 説明 | レコード目安 |
|---|------------|------|-------------|
| 1 | tournaments | 大会情報 | 1件/年 |
| 2 | groups | グループ（A,B,C,D） | 4件/大会 |
| 3 | teams | チーム | 24件/大会 |
| 4 | players | 選手 | 600-1200件/大会 |
| 5 | venues | 会場 | 4-5件/大会 |
| 6 | matches | 試合 | 約72件/大会 |
| 7 | goals | 得点 | 約200件/大会 |
| 8 | standings | 順位表 | 24件/大会 |
| 9 | exclusion_pairs | 対戦除外ペア | 12件/大会 |
| 10 | users | ユーザー | 5-10件 |
| 11 | report_recipients | 報告書送信先 | 4件/大会 |

---

## 各テーブル詳細

### 1. tournaments（大会）

```sql
CREATE TABLE tournaments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(200) NOT NULL,      -- 大会名
    edition         INTEGER NOT NULL DEFAULT 1,  -- 開催回数（第○回）
    year            INTEGER NOT NULL,            -- 開催年度
    start_date      DATE NOT NULL,               -- 開始日
    end_date        DATE NOT NULL,               -- 終了日
    match_duration  INTEGER NOT NULL DEFAULT 50, -- 試合時間（分）
    half_duration   INTEGER NOT NULL DEFAULT 25, -- ハーフタイム（分）
    interval_minutes INTEGER NOT NULL DEFAULT 15,-- 試合間インターバル（分）
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME NOT NULL
);
```

**ビジネスルール:**
- 年度ごとに1レコード
- 3日間開催（Day1-2: 予選、Day3: 決勝T）

---

### 2. groups（グループ）

```sql
CREATE TABLE groups (
    tournament_id   INTEGER NOT NULL,
    id              VARCHAR(1) NOT NULL,         -- 'A', 'B', 'C', 'D'
    name            VARCHAR(50) NOT NULL,        -- グループ名（表示用）
    venue_id        INTEGER,                     -- 担当会場
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME NOT NULL,
    PRIMARY KEY (tournament_id, id),
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
    FOREIGN KEY (venue_id) REFERENCES venues(id)
);
```

**ビジネスルール:**
- 4グループ固定（A, B, C, D）
- 各グループ6チーム
- 複合主キー: (tournament_id, id)

---

### 3. teams（チーム）

```sql
CREATE TABLE teams (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id   INTEGER NOT NULL,
    name            VARCHAR(100) NOT NULL,       -- チーム名
    short_name      VARCHAR(50),                 -- 略称（報告書用）
    team_type       ENUM('local', 'invited') NOT NULL DEFAULT 'invited',
    is_venue_host   BOOLEAN NOT NULL DEFAULT FALSE,  -- 会場担当校
    group_id        VARCHAR(1),                  -- 所属グループ
    group_order     INTEGER,                     -- グループ内番号(1-6)
    prefecture      VARCHAR(20),                 -- 都道府県
    notes           VARCHAR(500),
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME NOT NULL,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
    FOREIGN KEY (tournament_id, group_id) REFERENCES groups(tournament_id, id)
);
```

**ビジネスルール:**
- 24チーム固定
  - 地元チーム: 9チーム（会場担当校4校含む）
  - 招待チーム: 15チーム
- 会場担当校は各グループの1番に固定
  - A1: 浦和南、B1: 市立浦和、C1: 浦和学院、D1: 武南

**TeamType Enum:**
| 値 | 説明 |
|----|------|
| local | 地元チーム |
| invited | 招待チーム |

---

### 4. players（選手）

```sql
CREATE TABLE players (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id         INTEGER NOT NULL,
    number          INTEGER NOT NULL,            -- 背番号
    name            VARCHAR(100) NOT NULL,       -- 選手名
    grade           INTEGER,                     -- 学年（1-3）
    notes           VARCHAR(200),
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);
```

**ビジネスルール:**
- 1チーム26〜50名程度
- 得点者入力時のサジェストで使用

---

### 5. venues（会場）

```sql
CREATE TABLE venues (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id   INTEGER NOT NULL,
    name            VARCHAR(100) NOT NULL,       -- 会場名
    address         VARCHAR(300),                -- 住所
    group_id        VARCHAR(1),                  -- 担当グループID
    max_matches_per_day INTEGER NOT NULL DEFAULT 6,
    for_preliminary BOOLEAN NOT NULL DEFAULT TRUE,  -- 予選用
    for_final_day   BOOLEAN NOT NULL DEFAULT FALSE, -- 最終日用
    notes           VARCHAR(500),
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME NOT NULL,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
    FOREIGN KEY (tournament_id, group_id) REFERENCES groups(tournament_id, id)
);
```

**ビジネスルール:**
- 予選用会場（Day1-2）: 4会場
  - 浦和南高G、市立浦和高G、浦和学院G、武南高G
- 最終日用会場（Day3）:
  - 駒場スタジアム（1位リーグ）
  - その他3会場（研修試合）

---

### 6. matches（試合）

```sql
CREATE TABLE matches (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id   INTEGER NOT NULL,
    group_id        VARCHAR(1),
    venue_id        INTEGER NOT NULL,
    home_team_id    INTEGER NOT NULL,
    away_team_id    INTEGER NOT NULL,
    match_date      DATE NOT NULL,               -- 試合日
    match_time      TIME NOT NULL,               -- キックオフ時刻
    match_order     INTEGER NOT NULL,            -- 試合順
    stage           ENUM(...) NOT NULL DEFAULT 'preliminary',
    status          ENUM(...) NOT NULL DEFAULT 'scheduled',

    -- スコア
    home_score_half1 INTEGER,                    -- ホーム前半
    home_score_half2 INTEGER,                    -- ホーム後半
    home_score_total INTEGER,                    -- ホーム合計
    away_score_half1 INTEGER,                    -- アウェイ前半
    away_score_half2 INTEGER,                    -- アウェイ後半
    away_score_total INTEGER,                    -- アウェイ合計

    -- PK戦
    home_pk         INTEGER,
    away_pk         INTEGER,
    has_penalty_shootout BOOLEAN NOT NULL DEFAULT FALSE,

    -- 結果
    result          ENUM('home_win', 'away_win', 'draw'),

    -- ロック機能
    is_locked       BOOLEAN NOT NULL DEFAULT FALSE,
    locked_by       INTEGER,
    locked_at       DATETIME,

    -- 入力者
    entered_by      INTEGER,
    entered_at      DATETIME,

    -- 承認
    approval_status ENUM('pending', 'approved', 'rejected'),
    approved_by     INTEGER,
    approved_at     DATETIME,
    rejection_reason VARCHAR(500),

    notes           VARCHAR(500),
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME NOT NULL,

    FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
    FOREIGN KEY (tournament_id, group_id) REFERENCES groups(tournament_id, id),
    FOREIGN KEY (venue_id) REFERENCES venues(id),
    FOREIGN KEY (home_team_id) REFERENCES teams(id),
    FOREIGN KEY (away_team_id) REFERENCES teams(id),
    FOREIGN KEY (locked_by) REFERENCES users(id),
    FOREIGN KEY (entered_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);
```

**試合数:**
| ステージ | 試合数 | 日程 |
|----------|--------|------|
| 予選リーグ | 48試合 (12×4グループ) | Day1-2 |
| 準決勝 | 2試合 | Day3 |
| 3位決定戦 | 1試合 | Day3 |
| 決勝 | 1試合 | Day3 |
| 研修試合 | 約20試合 | Day3 |
| **合計** | **約72試合** | |

**MatchStage Enum:**
| 値 | 説明 |
|----|------|
| preliminary | 予選リーグ |
| semifinal | 準決勝 |
| third_place | 3位決定戦 |
| final | 決勝 |
| training | 研修試合 |

**MatchStatus Enum:**
| 値 | 説明 |
|----|------|
| scheduled | 予定 |
| in_progress | 試合中 |
| completed | 完了 |
| cancelled | 中止 |

**ApprovalStatus Enum:**
| 値 | 説明 |
|----|------|
| pending | 承認待ち |
| approved | 承認済み |
| rejected | 却下 |

---

### 7. goals（得点）

```sql
CREATE TABLE goals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id        INTEGER NOT NULL,
    team_id         INTEGER NOT NULL,
    player_id       INTEGER,                     -- 登録選手の場合
    player_name     VARCHAR(100) NOT NULL,       -- 得点者名（自由入力可）
    minute          INTEGER NOT NULL,            -- 得点時間（分）
    half            INTEGER NOT NULL,            -- 1=前半, 2=後半
    is_own_goal     BOOLEAN NOT NULL DEFAULT FALSE,
    is_penalty      BOOLEAN NOT NULL DEFAULT FALSE,
    notes           VARCHAR(200),
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME NOT NULL,
    FOREIGN KEY (match_id) REFERENCES matches(id),
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (player_id) REFERENCES players(id)
);
```

**ビジネスルール:**
- player_idは任意（登録外選手も得点可能）
- player_nameは必須（自由入力）

---

### 8. standings（順位表）

```sql
CREATE TABLE standings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id   INTEGER NOT NULL,
    group_id        VARCHAR(1) NOT NULL,
    team_id         INTEGER NOT NULL,
    rank            INTEGER NOT NULL DEFAULT 0,   -- 順位
    played          INTEGER NOT NULL DEFAULT 0,   -- 試合数
    won             INTEGER NOT NULL DEFAULT 0,   -- 勝利
    drawn           INTEGER NOT NULL DEFAULT 0,   -- 引分
    lost            INTEGER NOT NULL DEFAULT 0,   -- 敗北
    goals_for       INTEGER NOT NULL DEFAULT 0,   -- 総得点
    goals_against   INTEGER NOT NULL DEFAULT 0,   -- 総失点
    goal_difference INTEGER NOT NULL DEFAULT 0,   -- 得失点差
    points          INTEGER NOT NULL DEFAULT 0,   -- 勝点
    rank_reason     VARCHAR(100),                 -- 順位決定理由
    updated_at      DATETIME NOT NULL,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
    FOREIGN KEY (tournament_id, group_id) REFERENCES groups(tournament_id, id),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);
```

**順位決定ルール（優先順位）:**
1. 勝点（勝=3, 分=1, 負=0）
2. 得失点差
3. 総得点
4. 当該チーム間の対戦成績
5. 抽選

---

### 9. exclusion_pairs（対戦除外ペア）

```sql
CREATE TABLE exclusion_pairs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id   INTEGER NOT NULL,
    group_id        VARCHAR(1) NOT NULL,
    team1_id        INTEGER NOT NULL,
    team2_id        INTEGER NOT NULL,
    reason          VARCHAR(200),                -- 除外理由
    created_at      DATETIME NOT NULL,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
    FOREIGN KEY (tournament_id, group_id) REFERENCES groups(tournament_id, id),
    FOREIGN KEY (team1_id) REFERENCES teams(id),
    FOREIGN KEY (team2_id) REFERENCES teams(id)
);
```

**ビジネスルール（変則リーグ）:**
- 6チームで各チーム4試合（2チームとは対戦しない）
- 各グループ3組の除外ペアを設定
- 15対戦 - 3除外 = 12試合/グループ

**除外の判断基準:**
- 地元校同士の対戦を避ける
- 近い地域のチーム同士を避ける
- 他大会で同じリーグに所属するチーム同士を避ける

---

### 10. users（ユーザー）

```sql
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(50) NOT NULL UNIQUE, -- ログイン用
    password_hash   VARCHAR(255) NOT NULL,
    display_name    VARCHAR(100) NOT NULL,       -- 表示名
    email           VARCHAR(255),
    role            ENUM('admin', 'venue_staff', 'viewer') NOT NULL DEFAULT 'viewer',
    venue_id        INTEGER,                     -- 担当会場
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      DATETIME NOT NULL,
    updated_at      DATETIME NOT NULL,
    FOREIGN KEY (venue_id) REFERENCES venues(id)
);
```

**UserRole Enum:**
| 値 | 説明 | 権限 |
|----|------|------|
| admin | 管理者 | 全機能 |
| venue_staff | 会場担当者 | 担当会場の入力のみ |
| viewer | 閲覧者 | 閲覧のみ |

---

### 11. report_recipients（報告書送信先）

```sql
CREATE TABLE report_recipients (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id   INTEGER NOT NULL,
    name            VARCHAR(100) NOT NULL,       -- 送信先名
    email           VARCHAR(255),
    fax             VARCHAR(50),
    notes           VARCHAR(200),
    created_at      DATETIME NOT NULL,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id)
);
```

**固定送信先:**
- 埼玉新聞
- テレビ埼玉
- イシクラ
- 埼玉県サッカー協会

---

## リレーション図（詳細）

```
Tournament (1) ──────< (N) Group
    │                       │
    │                       │
    ├──────────< (N) Team ──┤
    │               │       │
    │               │       │
    ├──────< (N) Venue      │
    │           │           │
    │           │           │
    └──────< (N) Match ─────┘
                │
                │
                ├──────< (N) Goal
                │
                └──────> Standing

Tournament (1) ──< (N) ExclusionPair
Tournament (1) ──< (N) ReportRecipient
Venue (1) ──< (N) User
Team (1) ──< (N) Player
```

---

## インデックス推奨

```sql
-- 試合検索用
CREATE INDEX idx_matches_tournament_date ON matches(tournament_id, match_date);
CREATE INDEX idx_matches_venue ON matches(venue_id);
CREATE INDEX idx_matches_status ON matches(status);

-- 順位表検索用
CREATE INDEX idx_standings_tournament_group ON standings(tournament_id, group_id);

-- チーム検索用
CREATE INDEX idx_teams_tournament_group ON teams(tournament_id, group_id);

-- 得点検索用
CREATE INDEX idx_goals_match ON goals(match_id);
CREATE INDEX idx_goals_team ON goals(team_id);
```

---

## 注意事項

### 複合外部キー
以下のテーブルは複合外部キー `(tournament_id, group_id)` を使用:
- teams
- venues
- matches
- standings
- exclusion_pairs

### カスケード削除
- Tournament削除 → 関連する全データ削除
- Team削除 → Player, Goal, Standing削除
- Match削除 → Goal削除

### データ整合性
- 試合結果入力時に自動で順位表を更新
- 得点入力時にスコア合計を自動計算
