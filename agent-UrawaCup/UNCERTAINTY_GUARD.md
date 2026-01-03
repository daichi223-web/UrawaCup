# 不確実性ガード - 推測でコードを書かないためのガイド

## なぜ必要か？

「データは最初からそこにあるはずだ」「データはリスト形式で来るはずだ」という**推測（思い込み）**でコードを書くと、以下のようなエラーが発生します：

```
TypeError: venues.map is not a function
TypeError: Cannot read properties of undefined
```

## 2つの落とし穴

### 1. 時間差の落とし穴（タイミングの問題）

```
Reactが画面を描画する（一瞬）
  ↓
venues は初期値（null や undefined）の状態
  ↓
venues.map が走る → エラー！
  ↓
データがサーバーから届く（数ミリ秒後）
```

**推測**: 「画面を表示する時には、もうデータがあるだろう」
**現実**: データ取得は画面描画より遅い

### 2. データ構造の落とし穴（形の問題）

```
予想: [Venue A, Venue B, Venue C]

現実: { message: "Success", data: [Venue A, Venue B, ... ] }
```

**推測**: 「APIのレスポンスは配列そのものだろう」
**現実**: 配列は何かのプロパティ（.data や .venues）の中に入っていた

## 使い方

### 1. コーディング前に不確実性をチェック

```python
from agents import uncertainty_guard

# APIレスポンスの不確実性
issue = uncertainty_guard.check_api_response(
    endpoint="/api/venues",
    expected_type="Venue[]",
    method="GET",
)

# データ構造の不確実性
issue = uncertainty_guard.check_data_structure(
    context="会場一覧の表示",
    expected_structure="配列（Venue[]）",
    source="GET /api/venues",
)

# コーディング前のチェック
if uncertainty_guard.must_investigate_before_coding():
    print("調査を完了してからコーディングを再開してください。")
```

### 2. 調査を実行

Issueに記載された調査手順を実行：

1. `console.log()` で実際のレスポンスを確認
2. バックエンドのAPIエンドポイント定義を確認
3. 型定義ファイル（schemas/）を確認
4. 実際のJSONの構造をメモ

### 3. 調査結果を記録

```python
# 調査結果を記録
uncertainty_guard.record_findings(
    issue_id=1,
    findings="APIは { venues: [...], total: N } 形式で返す",
)

# Issueを解決
uncertainty_guard.resolve_issue(
    issue_id=1,
    correct_answer="response.data.venues でアクセスする必要がある",
)
```

## 必須チェックリスト

新しいデータを扱うときは、`.map()` を書く前に：

- [ ] `console.log(response)` で返ってきたデータが `[...]` なのか `{ data: [...] }` なのかを見た
- [ ] バックエンドのスキーマ定義を確認した
- [ ] 初期値を適切に設定した（`[]` または Loading 表示）
- [ ] Optional chaining (`?.`) を使用した
- [ ] 早期リターン（`if (!data) return ...`）を実装した

## Issue保存場所

- JSON: `Issues/UncertaintyIssues.json`
- Markdown: `Issues/UncertaintyIssues.md`

## 開発プロセス

```
1. 機能を実装しようとする
       ↓
2. データの取得・表示が必要
       ↓
3. 「このデータはどんな形で来るのか？」
       ↓
   ┌───────────────────┐
   │ 確信が持てない？  │
   └───────────────────┘
       ↓ Yes
4. UncertaintyGuard.create_issue() でIssue作成
       ↓
5. 調査手順に従って確認
       ↓
6. 調査結果を記録
       ↓
7. 確信を持ってコーディング
```

## 推測パターンの自動検出

以下のパターンがコード内にある場合、自動的に警告します：

| パターン | 説明 | 確認すべきこと |
|---------|------|---------------|
| `.map(` | 配列に対してmap使用 | 本当に配列か？ |
| `response.data` | レスポンスからdataを取得 | どんな構造か？ |
| `= []` | 空配列で初期化 | 適切な初期値か？ |
| `as Type[]` | 配列型としてキャスト | 本当に配列か？ |
