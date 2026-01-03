# 根本原因分析・確認事項レポート

**作成日**: 2026-01-01
**目的**: 推測で進めた箇所、根本的問題、明確化が必要な事項の整理

---

## 1. 推測で進めた箇所（確認が必要）

### 1.1 認証トークンの取得方法

**推測した内容:**
```typescript
const authData = localStorage.getItem('urawa-cup-auth');
const parsed = JSON.parse(authData);
const token = parsed.state.accessToken;
```

**根拠:**
- `authStore.ts` の persist 設定（179行目）で `'urawa-cup-auth'` をキーに保存
- partialize で `accessToken` を保存している

**確認が必要:**
- [ ] この構造が正しいか実際のlocalStorageの値を確認
- [ ] Zustand の persist middleware が `state` ラッパーを追加するか確認

---

### 1.2 APIフィールドの命名規則

**推測した内容:**
- バックエンドは全て camelCase で返す（CamelCaseModel 使用）
- リクエストも camelCase で送るべき

**確認が必要:**
- [ ] 全エンドポイントが CamelCaseModel を使用しているか
- [ ] 一部 snake_case のエンドポイントがないか
- [ ] バックエンドのスキーマ定義を確認

---

### 1.3 除外ペアの要件

**推測した内容:**
- 6チームの変則リーグでは3組の除外ペアが必要
- 15試合 - 3除外 = 12試合

**確認が必要:**
- [ ] これはビジネス要件として正しいか
- [ ] 除外ペアの選定基準は何か（地元同士を除外？）
- [ ] グループごとに異なるルールがあるか

---

## 2. 根本的な問題

### 2.1 APIクライアントの乱立（最重要）

**現状:**
```
src/frontend/src/
├── utils/
│   ├── api.ts          # axios instance A (認証あり、detail修正済み)
│   └── apiClient.ts    # axios instance B (認証あり、detail修正なし) ← ほぼ同じ
└── api/
    └── client.ts       # axios instance C (認証追加済み、別実装)
```

**問題点:**
1. 3つの異なるaxiosインスタンスが存在
2. `api.ts` と `apiClient.ts` はほぼ同じ内容（重複）
3. `client.ts` は異なる実装で別の機能（オフラインキュー）を持つ
4. 修正が1箇所に反映されても他に反映されない
5. どのページがどのクライアントを使うかが不明確

**使用状況:**
| ページ | 使用クライアント |
|--------|------------------|
| TeamManagement.tsx | `@/utils/api` |
| MatchSchedule.tsx | `@/utils/api` |
| MatchResult.tsx | `@/api/client` (matchApi経由) |
| Dashboard.tsx | 両方混在 |
| Standings.tsx | `@/api/client` (standingApi経由) |
| Settings.tsx | `@/utils/api` |

---

### 2.2 型定義と実装の乖離

**現状:**
```
src/shared/types/index.ts  →  snake_case で定義
バックエンド Pydantic      →  CamelCaseModel (camelCase出力)
フロントエンド実装         →  混在（両方使用）
```

**問題点:**
1. TypeScript型定義はsnake_case
2. 実際のAPIレスポンスはcamelCase
3. 型安全性が機能していない（any相当の動作）
4. IDEの補完が正しく動作しない
5. ランタイムエラーの原因

---

### 2.3 認証状態管理の分散

**現状:**
```typescript
// authStore.ts - ログイン時
api.defaults.headers.common['Authorization'] = `Bearer ${data.accessToken}`;

// api.ts/apiClient.ts - リクエスト時
const authData = localStorage.getItem('urawa-cup-auth');
// ... parsed.state.accessToken を使用

// client.ts - リクエスト時
const authData = localStorage.getItem('urawa-cup-auth');
// ... 同様の処理
```

**問題点:**
1. authStoreは `api` のみにヘッダーを設定（`apiClient`, `client`には設定されない）
2. 各クライアントが独自にlocalStorageから読み取り
3. ログアウト時に全クライアントからトークンが削除されるか不明
4. トークンリフレッシュが考慮されていない

---

### 2.4 エラーレスポンス形式の不統一

**現状:**
```typescript
// api.ts が期待する形式
{ error: { message: "..." } }

// FastAPIが返す形式
{ detail: "..." }

// 時々返る形式
{ detail: [{ msg: "...", loc: [...] }] }  // Pydantic validation error
```

**問題点:**
1. 各クライアントで異なるエラー処理
2. 一部だけ修正されて整合性がない
3. バリデーションエラーの配列形式が考慮されていない

---

## 3. コーディング上の問題

### 3.1 DRY原則違反

```
api.ts ≈ apiClient.ts（ほぼ同一ファイル）
```

- 同じコードが複数ファイルに存在
- 修正漏れが発生しやすい

### 3.2 単一責任原則違反

`client.ts` は複数の責任を持っている：
- HTTP通信
- 認証トークン管理
- オフラインキュー管理
- エラーハンドリング

### 3.3 型安全性の欠如

```typescript
// 実際のコード例
const gid = team.groupId || team.group_id;  // 両方試す
const teamType = team.teamType || team.team_type;  // 両方試す
```

- TypeScriptの型安全性が活かされていない
- ランタイムでの分岐が必要になっている

### 3.4 暗黙の依存関係

```typescript
// ページコンポーネントが直接localStorageを参照しない設計のはず
// だが、APIクライアントが暗黙的にlocalStorageに依存
```

---

## 4. 明確化が必要な事項

### 4.1 アーキテクチャに関する質問

| # | 質問 | 背景 |
|---|------|------|
| 1 | `api.ts` と `apiClient.ts` は統合すべきか？ | ほぼ同一内容で重複 |
| 2 | `@/api/client.ts` と `@/utils/api.ts` の役割分担は？ | 使い分けの意図が不明 |
| 3 | オフラインキュー機能は必要か？ | `client.ts`にのみ実装されている |
| 4 | 認証トークンの管理は誰の責任か？ | authStore? 各APIクライアント? |

### 4.2 命名規則に関する質問

| # | 質問 | 影響範囲 |
|---|------|----------|
| 1 | 全APIは camelCase で統一されているか？ | 型定義の方針決定 |
| 2 | `@shared/types` を camelCase に統一してよいか？ | 全ファイルの修正が必要 |
| 3 | バックエンドで snake_case を返すエンドポイントはあるか？ | フロントの対応方針 |

### 4.3 ビジネスロジックに関する質問

| # | 質問 | 現在の実装 |
|---|------|------------|
| 1 | 除外ペアの選定基準は何か？ | 不明（手動設定前提） |
| 2 | 各グループの除外数は固定（3組）か？ | 12試合固定を前提としている |
| 3 | 日程生成のやり直しは許可されるか？ | 現在は既存削除が必要 |

### 4.4 運用に関する質問

| # | 質問 | 関連 |
|---|------|------|
| 1 | 複数ブラウザ/タブでの同時使用は想定するか？ | WebSocket, localStorage |
| 2 | トークン有効期限とリフレッシュの仕様は？ | 認証エラー時の挙動 |
| 3 | オフライン時の動作は必要か？ | オフラインキュー機能 |

---

## 5. 推奨アクション（優先度順）

### 高優先度

1. **APIクライアントの統一**
   - `api.ts` と `apiClient.ts` を1つに統合
   - `@/api/client.ts` との役割を明確化
   - 全ページが同じクライアントを使用するよう修正

2. **型定義の camelCase 統一**
   - `@shared/types/index.ts` を全て camelCase に変換
   - フロントエンドコードの `|| snake_case` フォールバックを削除

3. **エラーハンドリングの統一**
   - FastAPI の `detail` 形式に統一対応
   - バリデーションエラーの配列形式も対応

### 中優先度

4. **認証フローの整理**
   - トークン管理を1箇所に集約
   - リフレッシュトークンの実装確認

5. **テストの追加**
   - APIクライアントの単体テスト
   - 認証フローの統合テスト

### 低優先度

6. **コードの整理**
   - 未使用インポートの削除
   - 不要なファイルの削除

---

## 6. 次のステップ

1. **この文書の確認をお願いします**
   - 質問事項に対する回答
   - 推奨アクションの優先度調整

2. **確認後の作業**
   - 回答に基づいてアーキテクチャ決定
   - 統一的な修正の実施

---

## 補足: 現在の私の判断基準

以下は確認なしに進めた判断です：

| 判断 | 根拠 | リスク |
|------|------|--------|
| localStorage のキーは `'urawa-cup-auth'` | authStore.ts の persist 設定を参照 | 低 |
| トークンは `parsed.state.accessToken` | Zustand persist の一般的な挙動 | 中（要確認） |
| APIは camelCase | CamelCaseModel の使用を確認 | 中（例外があるかも） |
| 除外ペアは3組/グループ | エラーメッセージから推測 | 高（ビジネス要件） |
