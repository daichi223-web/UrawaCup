# UrawaCup エラー分析・解決レポート

**作成日**: 2026-01-01
**対象**: フロントエンド・バックエンド連携の問題

---

## 1. チーム編集が保存されない問題

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

## 2. 日程生成 400 Bad Request エラー

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

## 3. 試合結果入力 401 Unauthorized エラー

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

## 4. APIエラーメッセージが表示されない問題

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

## 修正ファイル一覧

| ファイル | 修正内容 |
|----------|----------|
| `src/frontend/src/pages/TeamManagement.tsx` | editForm初期化、camelCase対応 |
| `src/frontend/src/utils/api.ts` | FastAPI detailフィールド対応 |
| `src/frontend/src/api/client.ts` | 認証インターセプター追加、エラーメッセージ改善 |
| `src/frontend/src/pages/MatchResult.tsx` | エラーメッセージ表示改善 |

---

## 教訓・ベストプラクティス

### 1. API通信の一貫性
- 複数のaxiosインスタンスを使用する場合、認証処理を統一すること
- 可能であれば単一のAPIクライアントを使用する

### 2. エラーハンドリング
- バックエンドのエラーレスポンス形式を確認し、フロントエンドで正しく抽出する
- FastAPIは`detail`フィールドを使用することを念頭に置く

### 3. フィールド名の命名規則
- バックエンド（Python）: snake_case
- フロントエンド（TypeScript）: camelCase
- Pydanticの`CamelCaseModel`を使用している場合、APIリクエスト/レスポンスはcamelCaseで統一

### 4. 変則リーグの要件
- 6チームの変則リーグでは、15試合中3試合を除外して12試合とする
- 除外ペアを事前に設定してから日程生成を実行する

---

## 5. 順位表（リーグ表）表示問題 - snake_case vs camelCase 不一致

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

#### C. 全型定義のcamelCase対応リスト

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

### 進行状況

- [x] Standing型をcamelCaseに修正
- [x] Standings.tsxのプロパティアクセスを修正
- [x] PublicStandings.tsxのプロパティアクセスを修正
- [ ] 全型定義をcamelCaseに統一
- [ ] 全フロントエンドコードを更新

### 備考

バックエンドのPydanticスキーマは既に`CamelCaseModel`を使用しており、JSONレスポンスはcamelCaseで返される。問題は共有型定義がsnake_caseで書かれていること。

一貫性のため、以下を推奨：
1. 共有型定義（`@shared/types`）をすべてcamelCaseに統一
2. フロントエンドコードをすべてcamelCaseでアクセスするよう修正
3. TypeScriptの型安全性を維持

---

## 6. WebSocket再接続問題

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

## 7. ビルドエラー一覧（2026-01-01時点）

### TypeScriptエラー概要

総エラー数: 約150件

#### カテゴリ別

| カテゴリ | 件数 | 主な原因 |
|----------|------|----------|
| snake_case vs camelCase不一致 | ~120件 | 型定義と実際のAPIレスポンスの不一致 |
| 未使用変数・インポート | ~15件 | import文やローカル変数の未使用 |
| 存在しないプロパティ | ~10件 | 型定義の不備 |
| その他 | ~5件 | - |

#### 修正優先度

1. **高**: 命名規則の統一（snake_case → camelCase）
2. **中**: 未使用インポートの削除
3. **低**: その他の型エラー

---

## まとめ

この問題の根本原因は、**バックエンド（Python/Pydantic）とフロントエンド（TypeScript）間での命名規則の不一致**である。

### 推奨解決アプローチ

1. `src/shared/types/index.ts`の全型定義をcamelCaseに変換
2. 各フロントエンドファイルのプロパティアクセスをcamelCaseに更新
3. 未使用インポートを削除
4. ビルド確認とテスト

---

## 関連ドキュメント

- **[RootCauseAnalysis.md](./RootCauseAnalysis.md)** - 根本原因分析・確認事項レポート
  - 推測で進めた箇所
  - APIクライアント乱立問題
  - 明確化が必要な質問リスト

- **[DatabaseStructure.md](./DatabaseStructure.md)** - データベース構造
  - 全11テーブルの定義
  - リレーション図
  - ビジネスルール

- **[../Requirement/RequirementSpecification.md](../Requirement/RequirementSpecification.md)** - 要件定義書
  - システム概要
  - 機能要件
  - 技術スタック
  - API設計
