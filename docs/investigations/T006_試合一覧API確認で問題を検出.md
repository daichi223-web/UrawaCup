# 調査レポート: 試合一覧API確認で問題を検出

## 基本情報

| 項目 | 値 |
|------|-----|
| イシューID | T006 |
| カテゴリ | match |
| タイプ | QUESTION |
| テスト名 | 試合一覧API確認 |
| ステータス | resolved |
| 調査日時 | 2026-01-04 07:51:39 |

## 元のイシュー詳細

なエンドポイントを確認します。
エンドポイントのリストを確認できました。`/api/matches/` というパスで試合一覧APIがあるようです。正しいURLでテストし直します。
## テスト結果報告

### 1. 実行結果

**リクエスト**: `curl http://localhost:8000/matches?tournament_id=1`  
**結果**: ❌ `{"detail":"Not Found"}`

**正しいエンドポイント**: `curl http://localhost:8000/api/matches/?tournament_id=1`  
**結果**: ✅ 成功

### 2. JSONレスポンスの確認
✅ 有効なJSONレスポンスが返されました。

### 3. matchesフィールドの確認
✅ `matches` フィールドが存在し、試合データの配列が含まれています。

### 問題点と報告

| 項目 | 状態 | 詳細 |
|------|------|------|
| エンドポイントパス | ⚠️ 要修正 | `/matches` ではなく `/api/matches/` が正しいパス |
| レスポンス形式 | ✅ OK | 正しいJSON形式 |
| matchesフィールド | ✅ OK | 配列として存在 |
| データ内容 | ✅ OK | 複数の試合データを取得（チーム情報、得点者情報含む） |

### レスポンス構造の概要
```json
{
  "matches": [
    {
      "id": 1,
      "tournamentId": 1,
      "groupId": "A",
      "homeTeam": {...},
      "awayTeam": {...},
      "venue": {...},
      "goals": [...],
      ...
    },
    ...
  ]
}
```

### 結論
- **API自体は正常に動作しています**
- ただし、指定されたURL（`/matches`）ではなく、`/api/matches/` が正しいエンドポイントです
- ドキュメントまたはリクエストURLを確認してください

## 調査結果

調査が完了しました。以下に結果をまとめます。

---

### 調査結果

**根本原因**: テストシナリオで使用されていたパスとAPIの実際のパスの不一致

このイシューは**実装上の問題ではなく、テスト仕様の誤り**です。

| 項目 | 状態 |
|------|------|
| バックエンド設計 | ✅ 正しい - `/api` プレフィックスでルーター登録 |
| フロントエンド設計 | ✅ 正しい - httpClientのbaseURLに `/api` を設定 |
| テストシナリオ | ❌ 誤り - `/api` プレフィックスなしでテスト実行 |

**APIパスの構造:**
```
/api (main.pyでprefix設定) + /matches (routes/__init__.pyでprefix設定) + / (matches.pyで定義) 
= /api/matches/
```

---

### 関連コード

| ファイル | 行 | 内容 |
|----------|-----|------|
| `D:/UrawaCup/src/backend/main.py` | 52 | `app.include_router(api_router, prefix="/api")` |
| `D:/UrawaCup/src/backend/routes/__init__.py` | 32 | `api_router.include_router(matches_router, prefix="/matches", tags=["試合管理"])` |
| `D:/UrawaCup/src/backend/routes/matches.py` | 49 | `@router.get("/", response_model=MatchList)` |
| `D:/UrawaCup/src/frontend/src/core/http/client.ts` | 9 | `baseURL: import.meta.env.VITE_API_BASE_URL || '/api'` |
| `D:/UrawaCup/src/frontend/src/features/matches/api.ts` | 25 | `const response = await httpClient.get<Match[]>('/matches', { params });` |

---

### 解決策

**推奨アプローチ**: テストとドキュメントの修正（コード変更不要）

1. **テストシナリオの修正**: 
   - ❌ `http://localhost:8000/matches?tournament_id=1`
   - ✅ `http://localhost:8000/api/matches/?tournament_id=1`

2. **ドキュメントの更新**: APIベースURLに `/api` プレフィックスが必須であることを明記

現在の実装は業界標準のRESTful設計に従っており、すべてのAPI（`/api/teams/`、`/api/venues/`など）が統一された設計になっています。

---

### 修正コード例

**テストコマンドの修正**:
```bash
# 修正前（失敗する）
curl "http://localhost:8000/matches?tournament_id=1"

# 修正後（成功する）
curl "http://localhost:8000/api/matches/?tournament_id=1"
```

**ドキュメント追記例**:
```markdown
## APIベースURL

すべてのエンドポイントは `/api` プレフィックス付きです。

- ベースURL: `http://localhost:8000/api`
- 試合一覧: `GET /api/matches/`
- チーム一覧: `GET /api/teams/`
- 会場一覧: `GET /api/venues/`
```

---

### ステータス

**resolved**

理由：
- API実装自体は正常に動作している
- 問題はテスト時のURL指定ミスであり、実装修正は不要
- 正しいパス（`/api/matches/`）を使用すれば正常にレスポンスが返される

---
*このレポートは agent-Investigate によって自動生成されました*
