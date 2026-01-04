# 調査レポート: 会場一覧API確認で問題を検出

## 基本情報

| 項目 | 値 |
|------|-----|
| イシューID | T003 |
| カテゴリ | venue |
| タイプ | QUESTION |
| テスト名 | 会場一覧API確認 |
| ステータス | error |
| 調査日時 | 2026-01-04 20:09:23 |

## 元のイシュー詳細

PI仕様に "venue" の文字列が見つかりませんでした。APIのpathsを全て確認してみましょう。
`/api/venues/`エンドポイントが見つかりました！正しいパスでテストしてみましょう。
## テスト結果報告

### 1. APIリクエストの実行

**注意**: 指定されたパス `/venues` ではなく、正しいパスは `/api/venues/` でした。

実行コマンド：
```bash
curl http://localhost:8000/api/venues/?tournament_id=1
```

### 2. JSONレスポンス確認 ✅

正常なJSONレスポンスが返されました。

### 3. 会場データ ✅

5つの会場データが含まれています：
| ID | 会場名 | グループ | 予選用 | 最終日用 | 決勝会場 |
|----|--------|----------|--------|----------|----------|
| 5 | 駒場スタジアム | - | ✅ | ✅ | ✅ |
| 1 | VenueA | A | ✅ | ❌ | ❌ |
| 2 | VenueB | B | ✅ | ❌ | ❌ |
| 3 | VenueC | C | ✅ | ❌ | ❌ |
| 4 | VenueD | D | ✅ | ❌ | ❌ |

### 4. 必須フィールドの確認 ✅

- **`forFinalDay`** フィールド: ✅ 存在する（camelCase形式）
- **`isFinalsVenue`** フィールド: ✅ 存在する（camelCase形式）

### 問題点

1. **エンドポイントのパスが異なる**: 指定された `http://localhost:8000/venues?tournament_id=1` ではなく、`http://localhost:8000/api/venues/?tournament_id=1` が正しいパスです。

2. **フィールド名の形式**: リクエストで期待されたスネークケース（`for_final_day`, `is_finals_venue`）ではなく、APIはキャメルケース（`forFinalDay`, `isFinalsVenue`）で返しています。

## 調査結果

調査中にエラーが発生: Command failed with exit code 3221226505 (exit code: 3221226505)
Error output: Check stderr output for details

---
*このレポートは agent-Investigate によって自動生成されました*
