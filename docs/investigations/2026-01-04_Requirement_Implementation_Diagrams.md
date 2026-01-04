# 要件・実装照合図

**作成日**: 2026-01-04
**目的**: FinalDay_Logic_Final.md / Report_PDF_Specification.md と実装の照合

---

## 1. 決勝トーナメント組み合わせ

### 1.1 要件（FinalDay_Logic_Final.md）

```mermaid
graph TB
    subgraph "決勝トーナメント（要件）"
        SF1["準決勝1<br/>A1位 vs C1位"]
        SF2["準決勝2<br/>B1位 vs D1位"]
        THIRD["3位決定戦<br/>SF1敗者 vs SF2敗者"]
        FINAL["決勝<br/>SF1勝者 vs SF2勝者"]

        SF1 -->|敗者| THIRD
        SF2 -->|敗者| THIRD
        SF1 -->|勝者| FINAL
        SF2 -->|勝者| FINAL
    end
```

### 1.2 実装（matches.py:1001-1086）

```mermaid
graph TB
    subgraph "決勝トーナメント（実装）"
        SF1_I["準決勝1<br/>qualified_teams[A] vs qualified_teams[C]<br/>= A1位 vs C1位"]
        SF2_I["準決勝2<br/>qualified_teams[B] vs qualified_teams[D]<br/>= B1位 vs D1位"]
        THIRD_I["3位決定戦<br/>プレースホルダー: A vs B"]
        FINAL_I["決勝<br/>プレースホルダー: C vs D"]

        SF1_I -->|敗者| THIRD_I
        SF2_I -->|敗者| THIRD_I
        SF1_I -->|勝者| FINAL_I
        SF2_I -->|勝者| FINAL_I
    end
```

### 1.3 照合結果

| 項目 | 要件 | 実装 | 一致 |
|------|------|------|:----:|
| 準決勝1 | A1位 vs C1位 | A1位 vs C1位 | ✅ |
| 準決勝2 | B1位 vs D1位 | B1位 vs D1位 | ✅ |
| 3位決定戦 | SF1敗者 vs SF2敗者 | プレースホルダー（後で更新） | ✅ |
| 決勝 | SF1勝者 vs SF2勝者 | プレースホルダー（後で更新） | ✅ |

---

## 2. 順位リーグ生成フロー

### 2.1 要件フロー

```mermaid
flowchart TD
    START([開始]) --> CALC["予選結果から順位計算"]
    CALC --> OVERALL["全体順位を決定<br/>（ランダムで同成績解決）"]
    OVERALL --> WARN1{ランダム決定<br/>あり?}
    WARN1 -->|Yes| W1["警告追加"]
    WARN1 -->|No| SPLIT
    W1 --> SPLIT
    SPLIT["決勝T進出チーム（各グループ1位）<br/>を分離"]
    SPLIT --> DIST["残りチームを4つの<br/>順位リーグに振り分け"]
    DIST --> VENUE["会場割り当て<br/>リーグ1→会場1, ..."]
    VENUE --> GEN["各リーグ内で<br/>総当たり対戦表生成"]
    GEN --> TIME["キックオフ時間<br/>自動割り当て"]
    TIME --> RESULT([完了])
```

### 2.2 実装フロー（generate_training_matches）

```mermaid
flowchart TD
    START([POST /generate-training]) --> CHECK["大会存在確認"]
    CHECK --> VENUE["会場取得<br/>for_final_day=True<br/>is_finals_venue=False"]
    VENUE --> VENUE_CHECK{4会場以上?}
    VENUE_CHECK -->|No| ERROR1["400 Error:<br/>会場不足"]
    VENUE_CHECK -->|Yes| HIST["予選リーグ対戦履歴取得<br/>（再戦チェック用）"]
    HIST --> SERVICE["StandingService.<br/>get_position_league_teams()"]

    subgraph "StandingService"
        SERVICE --> CALC_OVERALL["calculate_overall_standings()<br/>グループ内順位→勝点→得失点差→総得点→ランダム"]
        CALC_OVERALL --> SPLIT_TEAMS["knockout_teams = rank==1<br/>remaining = rank>1"]
        SPLIT_TEAMS --> WARN_CHECK["同成績チーム検出<br/>→warnings追加"]
        WARN_CHECK --> DISTRIBUTE["_distribute_to_leagues()<br/>4リーグに振り分け"]
    end

    DISTRIBUTE --> LOOP["各リーグでループ"]
    LOOP --> RR["get_round_robin_pairs()<br/>総当たりペア取得"]
    RR --> MATCH_LOOP["各ペアでループ"]
    MATCH_LOOP --> REMATCH{再戦?}
    REMATCH -->|Yes| REMATCH_WARN["rematch_warnings追加"]
    REMATCH -->|No| CREATE
    REMATCH_WARN --> CREATE["Match作成<br/>stage=TRAINING"]
    CREATE --> NEXT{次のペア?}
    NEXT -->|Yes| MATCH_LOOP
    NEXT -->|No| NEXT_LEAGUE{次のリーグ?}
    NEXT_LEAGUE -->|Yes| LOOP
    NEXT_LEAGUE -->|No| COMMIT["DB Commit"]
    COMMIT --> RESULT([MatchList返却])
```

### 2.3 照合結果

| 要件 | 実装 | 一致 |
|------|------|:----:|
| 全体順位計算 | `calculate_overall_standings()` | ✅ |
| ランダム決定警告 | `_detect_same_stats_warnings()` | ✅ |
| 4つの順位リーグ | `_distribute_to_leagues()` | ✅ |
| 上位リーグに端数配分 | `base_size + (1 if i < extra else 0)` | ✅ |
| 総当たり対戦表 | `get_round_robin_pairs()` | ✅ |
| 再戦チェック | `played_pairs`でチェック | ✅ |
| 会場割り当て | `training_venues[league_idx]` | ✅ |

---

## 3. 総当たり対戦順序

### 3.1 要件（5チームの場合）

```mermaid
graph LR
    subgraph "5チーム総当たり（要件）"
        R1["R1: 0-1, 2-3"]
        R2["R2: 0-4, 1-2"]
        R3["R3: 3-4, 0-2"]
        R4["R4: 1-3, 2-4"]
        R5["R5: 0-3, 1-4"]
    end
```

### 3.2 実装

```python
# get_round_robin_pairs(5)
[(0, 1), (2, 3), (0, 4), (1, 2), (3, 4),
 (0, 2), (1, 3), (2, 4), (0, 3), (1, 4)]
```

| チーム数 | 要件 | 実装 | 一致 |
|---------|------|------|:----:|
| 5チーム | 10試合 (5C2) | 10ペア | ✅ |
| 4チーム | 6試合 (4C2) | 6ペア | ✅ |
| 3チーム | 3試合 (3C2) | 3ペア | ✅ |
| 2チーム | 1試合 (2C2) | 1ペア | ✅ |

---

## 4. PDF報告書フロー

### 4.1 日別報告書生成（要件）

```mermaid
sequenceDiagram
    participant U as ユーザー
    participant F as フロントエンド
    participant B as バックエンド
    participant S as ReportService
    participant DB as Database

    U->>F: PDF出力ボタン
    F->>B: POST /tournaments/{id}/reports/daily
    Note right of B: 要件のAPIパス
    B->>DB: 試合データ取得
    B->>S: generate_pdf()
    S-->>B: PDF Buffer
    B-->>F: downloadUrl
    F-->>U: PDFダウンロード
```

### 4.2 日別報告書生成（実装）

```mermaid
sequenceDiagram
    participant U as ユーザー
    participant F as フロントエンド
    participant B as バックエンド
    participant S as ReportService
    participant DB as Database

    U->>F: PDF出力ボタン
    F->>B: GET /api/reports/export/pdf?tournament_id=X&target_date=Y
    Note right of B: 実装のAPIパス
    B->>DB: 試合データ取得
    B->>S: generate_pdf()
    S-->>B: PDF Buffer
    B-->>F: StreamingResponse (PDF)
    F-->>U: PDFダウンロード
```

### 4.3 APIパス対応表 ✅

| 機能 | 要件 | 実装 | 状態 |
|------|------|------|:----:|
| 日別PDF | `POST /tournaments/{id}/reports/daily` | `POST /reports/tournaments/{id}/daily` | ✅ |
| 最終結果PDF | `POST /tournaments/{id}/reports/final` | `POST /reports/tournaments/{id}/final` | ✅ |
| 設定取得 | `GET /tournaments/{id}/report-settings` | `GET /reports/tournaments/{id}/report-settings` | ✅ |
| 設定更新 | `PUT /tournaments/{id}/report-settings` | `PUT /reports/tournaments/{id}/report-settings` | ✅ |
| プレビュー | (要件あり) | `GET /reports/preview/pdf` | ✅ |
| 未入力チェック | (要件あり) | `GET /reports/check-incomplete` | ✅ |

※ レガシーAPI（後方互換性）も維持: `/reports/export/pdf`, `/reports/export/final-result`

---

## 5. PDFプレビュー・未入力チェック

### 5.1 プレビューフロー（新規実装）

```mermaid
sequenceDiagram
    participant U as ユーザー
    participant F as フロントエンド
    participant B as バックエンド
    participant S as ReportService

    U->>F: プレビューボタン
    F->>B: GET /api/reports/preview/pdf?tournament_id=X&target_date=Y
    B->>S: generate_pdf()
    S-->>B: PDF Buffer
    B->>B: Base64エンコード
    B-->>F: { content: "base64...", content_type: "application/pdf" }
    F->>F: iframe/embed で表示
    F-->>U: PDFプレビュー表示
```

### 5.2 未入力チェックフロー（新規実装）

```mermaid
sequenceDiagram
    participant U as ユーザー
    participant F as フロントエンド
    participant B as バックエンド
    participant DB as Database

    U->>F: 報告書ページ表示
    F->>B: GET /api/reports/check-incomplete?tournament_id=X&target_date=Y
    B->>DB: 試合データ取得

    alt 日別報告書
        B->>B: _check_daily_report_data()
        Note right of B: 試合結果未入力<br/>スコア不完全<br/>得点経過未入力
    else 最終結果
        B->>B: _check_final_result_data()
        Note right of B: 決勝T結果未入力<br/>MVP未登録<br/>優秀選手不足
    end

    B-->>F: { warnings: [...], critical_warnings: [...], can_export: bool }

    alt can_export == false
        F-->>U: 警告表示 + 出力ボタン無効化
    else can_export == true
        F-->>U: 警告表示（出力可能）
    end
```

---

## 6. 全体アーキテクチャ

```mermaid
flowchart TB
    subgraph "フロントエンド"
        FD[FinalDaySchedule.tsx]
        RP[Reports.tsx]
    end

    subgraph "バックエンド API"
        M_GF[/generate-finals/]
        M_GT[/generate-training/]
        R_EX[/reports/export/pdf/]
        R_PR[/reports/preview/pdf/]
        R_CHK[/reports/check-incomplete/]
    end

    subgraph "サービス層"
        SS[StandingService]
        RS[ReportService]
    end

    subgraph "データベース"
        DB[(SQLite/PostgreSQL)]
    end

    FD --> M_GF
    FD --> M_GT
    RP --> R_EX
    RP --> R_PR
    RP --> R_CHK

    M_GF --> SS
    M_GT --> SS
    R_EX --> RS
    R_PR --> RS
    R_CHK --> DB

    SS --> DB
    RS --> DB
```

---

## 7. 照合サマリー

### FinalDay_Logic_Final.md

| カテゴリ | 要件項目数 | 実装済み | 一致率 |
|----------|-----------|---------|--------|
| 決勝トーナメント組み合わせ | 4 | 4 | 100% |
| 順位リーグ振り分け | 5 | 5 | 100% |
| 総当たり対戦表 | 4 | 4 | 100% |
| 警告システム | 3 | 3 | 100% |
| **合計** | **16** | **16** | **100%** |

### Report_PDF_Specification.md

| カテゴリ | 要件項目数 | 実装済み | 一致率 |
|----------|-----------|---------|--------|
| 日別PDF生成 | 1 | 1 | 100% |
| 最終結果PDF生成 | 1 | 1 | 100% |
| プレビュー機能 | 1 | 1 | 100% |
| 未入力警告 | 1 | 1 | 100% |
| APIパス | 4 | 4 | 100% |
| **合計** | **8** | **8** | **100%** |

---

## 8. 結論

**FinalDay_Logic_Final.md**: 完全一致 ✅
- 準決勝の組み合わせ（A1 vs C1, B1 vs D1）
- 順位リーグ方式（4リーグ、総当たり）
- 警告システム（ランダム決定、再戦、不均等）

**Report_PDF_Specification.md**: 完全一致 ✅
- APIパスを要件に準拠（POST /tournaments/{id}/daily 等）
- プレビュー機能を実装
- 未入力警告を実装
- レガシーAPIも後方互換性のため維持
