# 調査レポート: チーム一覧API確認で問題を検出

## 基本情報

| 項目 | 値 |
|------|-----|
| イシューID | T005 |
| カテゴリ | team |
| タイプ | QUESTION |
| テスト名 | チーム一覧API確認 |
| ステータス | resolved |
| 調査日時 | 2026-01-04 07:45:50 |

## 元のイシュー詳細

バーが起動しているか確認します。
サーバーは起動していますが、`/teams` エンドポイントが存在しないようです。利用可能なエンドポイントを確認します。
正しいエンドポイントがわかりました。`/api/teams/` です（`/teams` ではありません）。正しいURLで再度テストします。
## テスト結果レポート

### 1. APIエンドポイントについて
⚠️ **注意**: 指定されたURL `http://localhost:8000/teams?tournamentId=1` は存在しませんでした。

✅ **正しいエンドポイント**: `http://localhost:8000/api/teams/?tournament_id=1`
- パスは `/api/teams/`（`/teams` ではない）
- パラメータ名は `tournament_id`（`tournamentId` ではない）

## 調査結果

調査が完了しました。以下に結果をまとめます。

---

## 調査結果

### 根本原因

この問題は**設計上の仕様**であり、バグではありません。プロジェクトでは以下の設計方針が採用されています：

1. **バックエンドAPI**: すべてのエンドポイントに `/api` プレフィックスを付与
2. **パラメータ命名規則**: Python慣例に従い `snake_case`（`tournament_id`）
3. **フロントエンド**: HTTPインターセプターで `camelCase` ↔ `snake_case` の自動変換

ユーザーが直接 `/teams?tournamentId=1` にアクセスしようとしたため、以下の2つの問題が発生しました：
- `/api` プレフィックスがないため404エラー
- パラメータ名が `camelCase` のままでバックエンドに届かない

---

### 関連コード

| ファイル | 役割 |
|---------|------|
| `D:/UrawaCup/src/backend/main.py:52` | `app.include_router(api_router, prefix="/api")` - 全APIに `/api` プレフィックス付与 |
| `D:/UrawaCup/src/backend/routes/__init__.py:27` | チームルーターを `/teams` パスで登録 → 最終パス `/api/teams` |
| `D:/UrawaCup/src/backend/routes/teams.py:32` | `tournament_id: Optional[int] = Query(...)` - snake_caseでパラメータ定義 |
| `D:/UrawaCup/src/frontend/src/core/http/client.ts:9` | `baseURL: '/api'` - HTTPクライアントのベースURL設定 |
| `D:/UrawaCup/src/frontend/src/core/http/interceptors/transform.ts:46-55` | camelCase → snake_case の自動変換インターセプター |
| `D:/UrawaCup/src/frontend/src/features/teams/api.ts:14-15` | 公式APIクライアント実装（正しい方法） |

---

### 解決策

#### 現状認識
- **バックエンド**: 正しく実装済み ✅
- **フロントエンド公式API**: 正しく実装済み ✅
- **自動変換機構**: 正常動作 ✅

#### 推奨アクション

1. **ドキュメント整備**
   - API仕様書に `/api` プレフィックスが必須であることを明記
   - パラメータは `snake_case` で受け付けることを明記

2. **開発者ガイドラインの強化**
   - 直接URLを構築せず、公式APIクライアント（`features/*/api.ts`）を使用する規約を設定

3. **コードの統一**（任意）
   - 直接テンプレートリテラルでURLを構築している以下の箇所を公式APIクライアントに統一：
     - `pages/Dashboard.tsx:34`
     - `pages/TeamManagement.tsx:40, 128`
     - `pages/ExclusionSettings.tsx:169`
     - `stores/teamStore.ts:56`

---

### 修正コード例

既存の実装は正しいため、追加修正は不要です。ただし、ドキュメントやテスト時の参考として正しいアクセス方法を示します：

```typescript
// ✅ 正しいフロントエンドでの使用方法
import { teamApi } from '@/features/teams/api';

// チーム一覧取得（推奨）
const teams = await teamApi.getAll(tournamentId);

// または直接HTTPクライアントを使用する場合
import { httpClient } from '@/core/http/client';
const response = await httpClient.get('/teams', { 
  params: { tournamentId } // 自動的にtournament_idに変換される
});
```

```bash
# ✅ 直接APIをテストする場合の正しいURL
curl "http://localhost:8000/api/teams/?tournament_id=1"

# ❌ 間違った呼び出し方法
curl "http://localhost:8000/teams?tournamentId=1"
```

---

### ステータス

**resolved**

この問題はバグではなく、設計上の仕様（`/api` プレフィックス + snake_case パラメータ）と、テスト時の誤ったURL使用による混乱が原因でした。フロントエンドの公式APIクライアントを使用すれば、変換は自動的に行われます。

---
*このレポートは agent-Investigate によって自動生成されました*
