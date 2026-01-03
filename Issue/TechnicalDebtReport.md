# UrawaCup 技術的課題・エラー分析統合レポート

**作成日**: 2026-01-01
**最終更新**: 2026-01-01
**目的**: 発生したエラー、根本原因、推測で進めた箇所、明確化が必要な事項の統合整理

---

# Part 1: 発生したエラーと解決策

---

## 1.1 チーム編集が保存されない問題

### 症状
- チーム管理画面でグループ、チーム区分（地元/招待）、会場校の変更が保存されない
- 編集モーダルで保存ボタンを押しても、リロード後に元に戻る

### 原因分析
1. **editFormの初期化漏れ**: `teamType`フィールドがeditForm stateに含まれていなかった
2. **フィールド名の不一致**: APIリクエストでsnake_case（`group_id`, `team_type`）を使用していたが、バックエンドのPydanticスキーマはcamelCase（`groupId`, `teamType`）を期待していた

### 該当ファイル
- `src/frontend/src/pages/TeamManagement.tsx`

### 解決策
```typescript
// Before
const [editForm, setEditForm] = useState({ name: '', groupId: '' });

// After
const [editForm, setEditForm] = useState({
  name: '',
  groupId: '',
  teamType: 'invited',
  isVenueHost: false
});
```

```typescript
// Before (handleSave)
await api.patch(`/teams/${selectedTeam.id}`, {
  name: editForm.name,
  group_id: editForm.groupId || null,  // snake_case - NG
});

// After
await api.patch(`/teams/${selectedTeam.id}`, {
  name: editForm.name,
  groupId: editForm.groupId || null,   // camelCase - OK
  teamType: editForm.teamType,
  isVenueHost: editForm.isVenueHost,
});
```

---

## 1.2 日程生成 400 Bad Request エラー

### 症状
- コンソールに `/matches/generate-schedule/1` の400エラーが表示される
- 「リクエストが不正です」という汎用メッセージのみ表示

### 原因分析
1. **除外ペア未設定**: 変則リーグ方式では6チームで12試合（15試合 - 3除外）が必要
2. **エラーメッセージ**: バックエンドは「対戦数が12試合になりません」と返していたが、フロントエンドが`detail`フィールドを読み取っていなかった

### 該当ファイル
- `src/backend/routes/matches.py` (バックエンド検証ロジック)
- `src/frontend/src/utils/api.ts` (エラーハンドリング)

### 解決策

#### A. 除外ペアの作成（各グループ3組、計12組）
```bash
# APIで除外ペアを登録
POST /api/exclusions/
{
  "tournamentId": 1,
  "team1Id": X,
  "team2Id": Y
}
```

#### B. エラーメッセージの改善
```typescript
// Before (api.ts)
const errorMessage = data?.error?.message || getDefaultErrorMessage(status)

// After
const errorMessage = data?.detail || data?.error?.message || getDefaultErrorMessage(status)
```

### 備考
- 既に日程が生成されている場合: 「既に予選リーグの日程が作成されています。再生成する場合は既存の試合を削除してください。」
- 除外ペアが不足している場合: 「対戦数が12試合になりません」

---

## 1.3 試合結果入力 401 Unauthorized エラー

### 症状
- 試合結果入力ページでスコアを保存しようとすると401エラー
- コンソール: `/api/matches/1/score` が401を返す

### 原因分析
- **認証トークン未付与**: `client.ts`（matchApi用）に認証インターセプターがなかった
- `api.ts`には認証インターセプターがあったが、`client.ts`は別のaxiosインスタンスで認証処理がなかった

### 該当ファイル
- `src/frontend/src/api/client.ts`
- `src/frontend/src/pages/MatchResult.tsx`

### 解決策
```typescript
// client.ts に認証インターセプターを追加
client.interceptors.request.use(
  (config) => {
    const authData = localStorage.getItem('urawa-cup-auth');
    if (authData) {
      try {
        const parsed = JSON.parse(authData);
        if (parsed.state?.accessToken) {
          config.headers.Authorization = `Bearer ${parsed.state.accessToken}`;
        }
      } catch {
        // JSON パースエラーは無視
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);
```

---

## 1.4 APIエラーメッセージが表示されない問題

### 症状
- バックエンドから詳細なエラーメッセージが返されているが、フロントエンドでは汎用メッセージ（「リクエストが不正です」等）のみ表示

### 原因分析
- FastAPIは`detail`フィールドでエラーメッセージを返す
- フロントエンドは`error.message`フィールドを期待していた

### 該当ファイル
- `src/frontend/src/utils/api.ts`
- `src/frontend/src/api/client.ts`

### 解決策
両ファイルのレスポンスインターセプターを修正：

```typescript
// FastAPIのエラーレスポンス形式
// { "detail": "エラーメッセージ" }

// 修正後のエラー抽出ロジック
const errorMessage = data?.detail || data?.error?.message || getDefaultErrorMessage(status);
```

---

## 1.5 順位表（リーグ表）表示問題 - snake_case vs camelCase 不一致

**発生日**: 2026-01-01

### 症状
- 順位表ページ（/standings）でデータが正しく表示されない
- `standing.team_id`, `standing.goal_difference`などのプロパティがundefinedになる
- TypeScriptビルドエラー: 多数のプロパティ名不一致エラー

### 原因分析

#### 根本原因
フロントエンドとバックエンドの間で**命名規則の不一致**が発生している。

```
バックエンドモデル (Python): snake_case
  例: tournament_id, group_id, goal_difference

バックエンドスキーマ (Pydantic CamelCaseModel): camelCase出力
  例: tournamentId, groupId, goalDifference

共有型定義 (TypeScript): snake_case
  例: tournament_id, group_id, goal_difference

フロントエンドコード: 混在（snake_case使用だがAPIはcamelCase）
```

#### 影響範囲
- `Standing` 型: `team_id` → `teamId`, `goals_for` → `goalsFor` など
- `StandingWithTeam` 型: 同上
- `MatchWithDetails` 型: `home_team` → `homeTeam`, `home_score_total` → `homeScoreTotal` など
- `Team` 型: `group_id` → `groupId`, `team_type` → `teamType` など
- `Venue` 型: `group_id` → `groupId`, `max_matches_per_day` → `maxMatchesPerDay` など

### 該当ファイル

#### 型定義
- `src/shared/types/index.ts` - 共有型定義（snake_caseで定義されている）

#### フロントエンドページ
- `src/frontend/src/pages/Standings.tsx` - 順位表
- `src/frontend/src/pages/public/PublicStandings.tsx` - 公開順位表
- `src/frontend/src/pages/MatchSchedule.tsx` - 日程管理
- `src/frontend/src/pages/MatchResult.tsx` - 試合結果入力
- `src/frontend/src/pages/TeamManagement.tsx` - チーム管理
- `src/frontend/src/pages/Settings.tsx` - 設定
- `src/frontend/src/components/approval/*.tsx` - 承認関連

### 解決策

#### A. 共有型定義をcamelCaseに統一（推奨）

```typescript
// Before (snake_case)
export interface Standing {
  id: number;
  tournament_id: number;
  group_id: string;
  team_id: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  rank_reason?: string;
  updated_at: string;
}

// After (camelCase)
export interface Standing {
  id: number;
  tournamentId: number;
  groupId: string;
  teamId: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  rankReason?: string;
  updatedAt: string;
}
```

#### B. フロントエンドコードをcamelCaseで統一

```typescript
// Before
<tr key={standing.team_id}>
  <td>{standing.goal_difference}</td>
</tr>

// After
<tr key={standing.teamId}>
  <td>{standing.goalDifference}</td>
</tr>
```

### 進行状況

- [x] Standing型をcamelCaseに修正
- [x] Standings.tsxのプロパティアクセスを修正
- [x] PublicStandings.tsxのプロパティアクセスを修正
- [x] Team型をcamelCaseに修正（フォールバック付き）
- [x] Venue型をcamelCaseに修正（フォールバック付き）
- [x] Match/MatchWithDetails型をcamelCaseに修正（フォールバック付き）
- [ ] 全フロントエンドコードを更新

---

## 1.6 WebSocket再接続問題

**発生日**: 2026-01-01

### 症状
- WebSocketエラーがコンソールに連続して表示される
- 「WebSocket接続開始」→「WebSocketエラー」→「WebSocket切断」のループ
- ブラウザのリソースを消費

### 原因分析
- WebSocketサーバーが起動していない、または接続できない
- 再接続ロジックに試行回数制限がなかった

### 解決策

```typescript
// useWebSocket.ts に最大再接続回数を追加
const MAX_RECONNECT_ATTEMPTS = 5;
const reconnectAttemptsRef = useRef(0);

socket.onclose = (event) => {
  if (event.code !== 1000) {
    reconnectAttemptsRef.current += 1;

    if (reconnectAttemptsRef.current > MAX_RECONNECT_ATTEMPTS) {
      console.log('最大再接続試行回数に達しました。WebSocket接続を停止します。');
      return; // 再接続しない
    }

    // 再接続ロジック...
  }
};

socket.onopen = () => {
  reconnectAttemptsRef.current = 0; // 成功時にリセット
};
```

---

# Part 2: 根本的な問題（アーキテクチャ課題）

---

## 2.1 APIクライアントの乱立（最重要）

### 現状
```
src/frontend/src/
├── utils/
│   ├── api.ts          # axios instance A (認証あり、detail修正済み)
│   └── apiClient.ts    # axios instance B (認証あり、detail修正なし) ← ほぼ同じ
└── api/
    └── client.ts       # axios instance C (認証追加済み、別実装)
```

### 問題点
1. 3つの異なるaxiosインスタンスが存在
2. `api.ts` と `apiClient.ts` はほぼ同じ内容（重複）
3. `client.ts` は異なる実装で別の機能（オフラインキュー）を持つ
4. 修正が1箇所に反映されても他に反映されない
5. どのページがどのクライアントを使うかが不明確

### 使用状況
| ページ | 使用クライアント |
|--------|------------------|
| TeamManagement.tsx | `@/utils/api` |
| MatchSchedule.tsx | `@/utils/api` |
| MatchResult.tsx | `@/api/client` (matchApi経由) |
| Dashboard.tsx | 両方混在 |
| Standings.tsx | `@/api/client` (standingApi経由) |
| Settings.tsx | `@/utils/api` |

---

## 2.2 型定義と実装の乖離

### 現状
```
src/shared/types/index.ts  →  元はsnake_case（現在camelCaseに移行中）
バックエンド Pydantic      →  CamelCaseModel (camelCase出力)
フロントエンド実装         →  混在（両方使用）
```

### 問題点
1. TypeScript型定義は元々snake_case
2. 実際のAPIレスポンスはcamelCase
3. 型安全性が機能していない（any相当の動作）
4. IDEの補完が正しく動作しない
5. ランタイムエラーの原因

---

## 2.3 認証状態管理の分散

### 現状
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

### 問題点
1. authStoreは `api` のみにヘッダーを設定（`apiClient`, `client`には設定されない）
2. 各クライアントが独自にlocalStorageから読み取り
3. ログアウト時に全クライアントからトークンが削除されるか不明
4. トークンリフレッシュが考慮されていない

---

## 2.4 エラーレスポンス形式の不統一

### 現状
```typescript
// api.ts が期待する形式
{ error: { message: "..." } }

// FastAPIが返す形式
{ detail: "..." }

// 時々返る形式
{ detail: [{ msg: "...", loc: [...] }] }  // Pydantic validation error
```

### 問題点
1. 各クライアントで異なるエラー処理
2. 一部だけ修正されて整合性がない
3. バリデーションエラーの配列形式が考慮されていない

---

# Part 3: 推測で進めた箇所（確認が必要）

---

## 3.1 認証トークンの取得方法

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

## 3.2 APIフィールドの命名規則

**推測した内容:**
- バックエンドは全て camelCase で返す（CamelCaseModel 使用）
- リクエストも camelCase で送るべき

**確認が必要:**
- [ ] 全エンドポイントが CamelCaseModel を使用しているか
- [ ] 一部 snake_case のエンドポイントがないか
- [ ] バックエンドのスキーマ定義を確認

---

## 3.3 除外ペアの要件

**推測した内容:**
- 6チームの変則リーグでは3組の除外ペアが必要
- 15試合 - 3除外 = 12試合

**確認が必要:**
- [ ] これはビジネス要件として正しいか
- [ ] 除外ペアの選定基準は何か（地元同士を除外？）
- [ ] グループごとに異なるルールがあるか

---

# Part 4: コーディング上の問題

---

## 4.1 DRY原則違反

```
api.ts ≈ apiClient.ts（ほぼ同一ファイル）
```

- 同じコードが複数ファイルに存在
- 修正漏れが発生しやすい

## 4.2 単一責任原則違反

`client.ts` は複数の責任を持っている：
- HTTP通信
- 認証トークン管理
- オフラインキュー管理
- エラーハンドリング

## 4.3 型安全性の欠如

```typescript
// 実際のコード例
const gid = team.groupId || team.group_id;  // 両方試す
const teamType = team.teamType || team.team_type;  // 両方試す
```

- TypeScriptの型安全性が活かされていない
- ランタイムでの分岐が必要になっている

## 4.4 暗黙の依存関係

```typescript
// ページコンポーネントが直接localStorageを参照しない設計のはず
// だが、APIクライアントが暗黙的にlocalStorageに依存
```

---

# Part 5: 明確化が必要な事項

---

## 5.1 アーキテクチャに関する質問

| # | 質問 | 背景 |
|---|------|------|
| 1 | `api.ts` と `apiClient.ts` は統合すべきか？ | ほぼ同一内容で重複 |
| 2 | `@/api/client.ts` と `@/utils/api.ts` の役割分担は？ | 使い分けの意図が不明 |
| 3 | オフラインキュー機能は必要か？ | `client.ts`にのみ実装されている |
| 4 | 認証トークンの管理は誰の責任か？ | authStore? 各APIクライアント? |

## 5.2 命名規則に関する質問

| # | 質問 | 影響範囲 |
|---|------|----------|
| 1 | 全APIは camelCase で統一されているか？ | 型定義の方針決定 |
| 2 | `@shared/types` を camelCase に統一してよいか？ | 全ファイルの修正が必要 |
| 3 | バックエンドで snake_case を返すエンドポイントはあるか？ | フロントの対応方針 |

## 5.3 ビジネスロジックに関する質問

| # | 質問 | 現在の実装 |
|---|------|------------|
| 1 | 除外ペアの選定基準は何か？ | 不明（手動設定前提） |
| 2 | 各グループの除外数は固定（3組）か？ | 12試合固定を前提としている |
| 3 | 日程生成のやり直しは許可されるか？ | 現在は既存削除が必要 |

## 5.4 運用に関する質問

| # | 質問 | 関連 |
|---|------|------|
| 1 | 複数ブラウザ/タブでの同時使用は想定するか？ | WebSocket, localStorage |
| 2 | トークン有効期限とリフレッシュの仕様は？ | 認証エラー時の挙動 |
| 3 | オフライン時の動作は必要か？ | オフラインキュー機能 |

---

# Part 6: ビルドエラー一覧（2026-01-01時点）

---

## TypeScriptエラー概要

総エラー数: 約150件

### カテゴリ別

| カテゴリ | 件数 | 主な原因 |
|----------|------|----------|
| snake_case vs camelCase不一致 | ~120件 | 型定義と実際のAPIレスポンスの不一致 |
| 未使用変数・インポート | ~15件 | import文やローカル変数の未使用 |
| 存在しないプロパティ | ~10件 | 型定義の不備 |
| その他 | ~5件 | - |

### 全型定義のcamelCase対応リスト

| 型名 | snake_caseプロパティ | camelCase変換 |
|------|----------------------|---------------|
| Standing | tournament_id | tournamentId |
| Standing | group_id | groupId |
| Standing | team_id | teamId |
| Standing | goals_for | goalsFor |
| Standing | goals_against | goalsAgainst |
| Standing | goal_difference | goalDifference |
| Standing | rank_reason | rankReason |
| Standing | updated_at | updatedAt |
| Match | tournament_id | tournamentId |
| Match | group_id | groupId |
| Match | venue_id | venueId |
| Match | home_team_id | homeTeamId |
| Match | away_team_id | awayTeamId |
| Match | match_date | matchDate |
| Match | match_time | matchTime |
| Match | match_order | matchOrder |
| Match | home_score_half1 | homeScoreHalf1 |
| Match | home_score_half2 | homeScoreHalf2 |
| Match | home_score_total | homeScoreTotal |
| Match | away_score_* | awayScore* |
| Match | home_pk | homePK |
| Match | away_pk | awayPK |
| Match | has_penalty_shootout | hasPenaltyShootout |
| Match | is_locked | isLocked |
| Match | locked_by | lockedBy |
| Match | locked_at | lockedAt |
| Match | entered_by | enteredBy |
| Match | entered_at | enteredAt |
| Match | approval_status | approvalStatus |
| Match | approved_by | approvedBy |
| Match | approved_at | approvedAt |
| Match | rejection_reason | rejectionReason |
| Match | created_at | createdAt |
| Match | updated_at | updatedAt |
| MatchWithDetails | home_team | homeTeam |
| MatchWithDetails | away_team | awayTeam |
| Team | tournament_id | tournamentId |
| Team | short_name | shortName |
| Team | team_type | teamType |
| Team | is_venue_host | isVenueHost |
| Team | group_id | groupId |
| Team | group_order | groupOrder |
| Team | created_at | createdAt |
| Team | updated_at | updatedAt |
| Venue | tournament_id | tournamentId |
| Venue | group_id | groupId |
| Venue | max_matches_per_day | maxMatchesPerDay |
| Venue | for_preliminary | forPreliminary |
| Venue | for_final_day | forFinalDay |
| Venue | created_at | createdAt |
| Venue | updated_at | updatedAt |

---

# Part 7: 推奨アクション（優先度順）

---

## 高優先度

1. **APIクライアントの統一**
   - `api.ts` と `apiClient.ts` を1つに統合
   - `@/api/client.ts` との役割を明確化
   - 全ページが同じクライアントを使用するよう修正

2. **型定義の camelCase 統一**
   - `@shared/types/index.ts` を全て camelCase に変換 ✅ 完了
   - フロントエンドコードの `|| snake_case` フォールバックを削除

3. **エラーハンドリングの統一**
   - FastAPI の `detail` 形式に統一対応
   - バリデーションエラーの配列形式も対応

## 中優先度

4. **認証フローの整理**
   - トークン管理を1箇所に集約
   - リフレッシュトークンの実装確認

5. **テストの追加**
   - APIクライアントの単体テスト
   - 認証フローの統合テスト

## 低優先度

6. **コードの整理**
   - 未使用インポートの削除
   - 不要なファイルの削除

---

# Part 8: 修正ファイル一覧

---

| ファイル | 修正内容 | ステータス |
|----------|----------|------------|
| `src/frontend/src/pages/TeamManagement.tsx` | editForm初期化、camelCase対応 | ✅ 完了 |
| `src/frontend/src/utils/api.ts` | FastAPI detailフィールド対応 | ✅ 完了 |
| `src/frontend/src/api/client.ts` | 認証インターセプター追加、エラーメッセージ改善 | ✅ 完了 |
| `src/frontend/src/pages/MatchResult.tsx` | エラーメッセージ表示改善 | ✅ 完了 |
| `src/frontend/src/pages/Standings.tsx` | camelCaseプロパティアクセス | ✅ 完了 |
| `src/frontend/src/pages/public/PublicStandings.tsx` | camelCaseプロパティアクセス | ✅ 完了 |
| `src/frontend/src/hooks/useWebSocket.ts` | 再接続回数制限追加 | ✅ 完了 |
| `src/shared/types/index.ts` | Standing, Team, Venue, Match等をcamelCaseに変換 | ✅ 完了 |

---

# Part 9: 教訓・ベストプラクティス

---

## API通信の一貫性
- 複数のaxiosインスタンスを使用する場合、認証処理を統一すること
- 可能であれば単一のAPIクライアントを使用する

## エラーハンドリング
- バックエンドのエラーレスポンス形式を確認し、フロントエンドで正しく抽出する
- FastAPIは`detail`フィールドを使用することを念頭に置く

## フィールド名の命名規則
- バックエンド（Python）: snake_case
- フロントエンド（TypeScript）: camelCase
- Pydanticの`CamelCaseModel`を使用している場合、APIリクエスト/レスポンスはcamelCaseで統一

## 変則リーグの要件
- 6チームの変則リーグでは、15試合中3試合を除外して12試合とする
- 除外ペアを事前に設定してから日程生成を実行する

---

# Part 10: 現在のビルドエラー詳細分析（2026-01-01最新）

---

## エラー総数: 約28件

型定義の更新後、エラーは大幅に削減されました。残りのエラーを以下にカテゴリ別に分類します。

---

## 10.1 存在しないエクスポート (1件)

### ファイル: `src/api/teams.ts`
```
error TS2305: Module '"@shared/types"' has no exported member 'TeamList'.
```

**原因**: `TeamList`型が`@shared/types`から削除されたか、エクスポートされていない

**解決策**:
```typescript
// 選択肢A: TeamList型を@shared/typesに追加
export interface TeamList {
  teams: Team[];
  total: number;
}

// 選択肢B: teams.tsでインラインで定義
interface TeamListResponse {
  teams: Team[];
  total: number;
}
```

---

## 10.2 存在しないプロパティ (2件)

### ファイル: `src/api/teams.ts`
```
error TS2339: Property 'token' does not exist on type 'AuthState'.
```

**原因**: `AuthState`型に`token`プロパティがない（`accessToken`のはず）

**解決策**:
```typescript
// Before
state.token

// After
state.accessToken
```

### ファイル: `src/pages/Settings.tsx`
```
error TS2322: Type 'number | undefined' is not assignable to type 'number'.
```

**原因**: `venue.max_matches_per_day`（オプショナル）をnumberとして使用

**解決策**:
```typescript
// Before
maxMatchesPerDay: venue.max_matches_per_day

// After
maxMatchesPerDay: venue.max_matches_per_day ?? venue.maxMatchesPerDay ?? 6
```

---

## 10.3 未使用インポート/変数 (10件)

| ファイル | 未使用 | 解決策 |
|----------|--------|--------|
| ApprovalHistoryPanel.tsx | User | 削除 |
| ApprovalHistoryPanel.tsx | ApprovalStatus | 削除 |
| ApprovalHistoryPanel.tsx | ApprovalStatusBadge | 削除 |
| MatchApprovalPanel.tsx | formatMatchDateTime | 削除または使用 |
| MatchSchedule.tsx | MatchStage | 削除 |
| MatchSchedule.tsx | matchError | 削除または使用 |
| Reports.tsx | Mail | 削除 |
| Reports.tsx | AlertTriangle | 削除 |
| Reports.tsx | CheckCircle | 削除 |

**一括解決**:
```bash
# ESLintで自動修正可能
npx eslint --fix "src/**/*.{ts,tsx}"
```

---

## 10.4 型互換性エラー - LucideIcon (7件)

### ファイル: `src/components/Layout.tsx`
```
error TS2322: Type 'LucideIcon' is not assignable to type
'ComponentType<{ size?: number | undefined; className?: string | undefined; }>'
```

**原因**: `LucideIcon`の`size`プロパティが`string | number`だが、独自定義では`number`のみ

**解決策**:
```typescript
// Before
interface NavItem {
  icon: ComponentType<{ size?: number; className?: string }>;
}

// After
import { LucideIcon } from 'lucide-react';

interface NavItem {
  icon: LucideIcon;
}
```

---

## 10.5 存在しないプロパティ - PublicMatchList (8件)

### ファイル: `src/pages/public/PublicMatchList.tsx`

| 使用中のプロパティ | 正しいプロパティ |
|--------------------|------------------|
| kickoff_time | matchTime |
| home_score | homeScoreTotal |
| away_score | awayScoreTotal |
| home_pk_score | homePK |
| away_pk_score | awayPK |

**原因**: PublicMatchList.tsxがsnake_caseを使用しているが、型定義はcamelCase

**解決策**:
```typescript
// Before
match.kickoff_time
match.home_score
match.away_score

// After
match.matchTime
match.homeScoreTotal
match.awayScoreTotal
```

---

## 10.6 エラー修正優先度

| 優先度 | カテゴリ | 件数 | 修正難易度 |
|--------|----------|------|------------|
| 高 | PublicMatchList.tsx snake_case → camelCase | 8件 | 低 |
| 高 | teams.ts token → accessToken | 1件 | 低 |
| 中 | Layout.tsx LucideIcon型 | 7件 | 低 |
| 低 | 未使用インポート | 10件 | 低（自動修正可） |
| 低 | TeamList型の追加 | 1件 | 低 |
| 低 | Settings.tsx undefinedチェック | 1件 | 低 |

---

## 10.7 推奨修正順序

1. **PublicMatchList.tsx** - プロパティ名をcamelCaseに変更
2. **teams.ts** - `token` を `accessToken` に変更
3. **Layout.tsx** - NavItem型の`icon`を`LucideIcon`型に変更
4. **Settings.tsx** - nullish coalescing演算子でデフォルト値設定
5. **@shared/types** - `TeamList`型をエクスポートに追加
6. **各ファイル** - 未使用インポートを削除

---

## 10.8 自動修正可能なエラー

以下のコマンドで一部エラーを自動修正可能：

```bash
# 未使用インポートの削除
npx eslint --fix "src/**/*.{ts,tsx}"

# または TypeScript compiler オプション
# tsconfig.json に以下を追加で警告として扱う
{
  "compilerOptions": {
    "noUnusedLocals": false,  // 一時的に無効化
    "noUnusedParameters": false
  }
}
```

---

# 補足: 判断基準

以下は確認なしに進めた判断です：

| 判断 | 根拠 | リスク |
|------|------|--------|
| localStorage のキーは `'urawa-cup-auth'` | authStore.ts の persist 設定を参照 | 低 |
| トークンは `parsed.state.accessToken` | Zustand persist の一般的な挙動 | 中（要確認） |
| APIは camelCase | CamelCaseModel の使用を確認 | 中（例外があるかも） |
| 除外ペアは3組/グループ | エラーメッセージから推測 | 高（ビジネス要件） |
