# ユーザーフロー図（実装ベース）

## 1. 大会作成・設定フロー（実装）

```mermaid
flowchart TD
    A[ダッシュボード /] --> B[設定画面 /settings]
    B --> C[大会設定セクション]
    C --> D[大会名・略称・回数入力]
    D --> E[開始日・終了日入力]
    E --> F[試合時間・インターバル入力]
    F --> G[保存ボタン]
    G --> H[PATCH /tournaments/tournamentId]
    
    B --> I[会場設定セクション]
    I --> J[会場一覧表示]
    J --> K[編集ボタン]
    K --> L[会場編集モーダル]
    L --> M[PATCH /venues/id]
    
    J --> N[会場追加ボタン]
    N --> O[準備中 Toast表示]
    
    style N fill:#ffcccc
    style O fill:#ffcccc
```

**注**: 新規大会作成ボタンは未実装。既存大会の編集のみ。会場追加も準備中。

## 2. チーム登録フロー（実装）

```mermaid
flowchart TD
    A[ダッシュボード] --> B[チーム登録 クイックアクション]
    B --> C[チーム管理画面 /teams]
    
    C --> D[グループタブ選択]
    D --> E[チーム一覧テーブル表示]
    
    E --> F[チーム追加ボタン]
    F --> G[追加モーダル]
    G --> H[チーム名入力]
    H --> I[グループ選択]
    I --> J[区分選択 招待/地元]
    J --> K[会場担当チェック]
    K --> L[追加ボタン]
    L --> M[POST /teams/]
    
    E --> N[編集ボタン]
    N --> O[編集モーダル]
    O --> P[情報修正]
    P --> Q[保存ボタン]
    Q --> R[PATCH /teams/id]
    
    E --> S[CSVインポートボタン]
    S --> T[準備中 Toast表示]
    
    style S fill:#ffcccc
    style T fill:#ffcccc
```

**注**: CSVインポート機能はUI実装済みだがAPI連携は準備中。

## 3. 選手登録フロー（実装）

```mermaid
flowchart TD
    A[設定画面 /settings] --> B[選手データ管理セクション]
    B --> C[説明テキスト表示]
    C --> D[テンプレートダウンロードボタン]
    D --> E[準備中 Toast表示]
    
    C --> F[選手データインポートボタン]
    F --> G[準備中 Toast表示]
    
    style D fill:#ffcccc
    style E fill:#ffcccc
    style F fill:#ffcccc
    style G fill:#ffcccc
```

**注**: 選手管理機能は設計段階。UIボタンはあるが機能未実装。

## 4. 試合日程生成フロー（実装）

```mermaid
flowchart TD
    A[ダッシュボード] --> B[日程管理 クイックアクション]
    B --> C[日程管理画面 /schedule]
    
    C --> D[日付タブ選択]
    D --> E{Day1 or Day2?}
    E -->|Yes| F{予選試合なし?}
    F -->|Yes| G[予選リーグ日程を生成ボタン]
    G --> H[POST /matches/generate-schedule/tournamentId]
    H --> I[48試合生成]
    F -->|No| J[試合一覧表示]
    
    E -->|Day3| K{予選試合あり?}
    K -->|No| L[予選を先に生成]
    K -->|Yes| M{決勝試合なし?}
    M -->|Yes| N[決勝トーナメント生成ボタン]
    N --> O[POST /matches/generate-finals/tournamentId]
    O --> P[決勝T 4試合生成]
    
    M -->|No| Q{研修試合なし?}
    Q -->|Yes| R[研修試合生成ボタン]
    R --> S[POST /matches/generate-training/tournamentId]
    S --> T[研修試合生成]
    
    Q -->|No| U[組み合わせ更新ボタン]
    U --> V[PUT /matches/update-finals-bracket/tournamentId]
    
    J --> W[試合クリック]
    W --> X[結果入力画面 /results へ遷移]
```

## 5. スコア入力フロー（実装）

```mermaid
flowchart TD
    A[試合結果入力画面 /results] --> B[フィルタセクション]
    B --> C[日付選択 Day1/2/3]
    C --> D[会場選択]
    D --> E[状態フィルタ 全て/未入力/入力済み]
    E --> F[試合一覧表示]
    
    F --> G[結果入力ボタン or 修正ボタン]
    G --> H[結果入力モーダル]
    
    H --> I[ホーム前半スコア入力]
    I --> J[ホーム後半スコア入力]
    J --> K[アウェイ前半スコア入力]
    K --> L[アウェイ後半スコア入力]
    L --> M[合計スコア自動計算表示]
    
    M --> N{PK戦あり?}
    N -->|Yes| O[PKスコア入力]
    N -->|No| P[保存ボタン]
    O --> P
    
    P --> Q[PUT /matches/id/score]
    Q --> R[成功Toast表示]
    R --> S[一覧更新]
```

**注**: 得点者入力機能は実装されていない。排他ロック・バージョン競合検出も未実装。

## 6. 報告書作成フロー（実装）

```mermaid
flowchart TD
    A[報告書出力画面 /reports] --> B[出力条件セクション]
    B --> C[日付選択 Day1/2/3]
    C --> D[会場選択 全会場/各会場]
    D --> E[出力形式選択 PDF/Excel]
    
    E --> F{PDF選択?}
    F -->|Yes| G[PDFをダウンロードボタン]
    G --> H[GET /reports/export/pdf]
    H --> I[Blobダウンロード]
    
    F -->|No| J[Excelをダウンロードボタン]
    J --> K[GET /reports/export/excel]
    K --> L[Blobダウンロード]
    
    B --> M[送信先設定セクション]
    M --> N[Coming Soon 無効化]
    
    style N fill:#ffcccc
```

**注**: メール送信機能は Coming Soon。バックグラウンドジョブ・ポーリングは未実装（同期ダウンロード）。

## 7. 対戦除外設定フロー（実装）

```mermaid
flowchart TD
    A[対戦除外設定画面 /exclusions] --> B[グループタブ選択 A/B/C/D]
    B --> C[チームマトリクス表示]
    C --> D[除外トグルクリック]
    D --> E{除外追加?}
    E -->|Yes| F[POST /exclusions]
    E -->|No| G[DELETE /exclusions/id]
    F --> H[除外ペア追加]
    G --> I[除外ペア削除]
    
    H --> J{各チーム最大2つ制限チェック}
    I --> J
    J --> K[マトリクス更新]
```

## 8. 結果承認フロー（実装）

```mermaid
flowchart TD
    A[結果承認画面 /approval] --> B[承認待ち試合一覧]
    B --> C[スコア表示 PK含む]
    C --> D{アクション}
    D -->|承認| E[承認ボタン]
    E --> F[PATCH /matches/id/approve]
    D -->|却下| G[却下ボタン]
    G --> H[理由入力モーダル]
    H --> I[PATCH /matches/id/reject]
    F --> J[一覧更新]
    I --> J
```
