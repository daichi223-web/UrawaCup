# 会場設定ロジック - 現状まとめ

## 概要

会場（Venue）の設定には以下の重要なフラグがあります：

| フィールド名 | 説明 | デフォルト |
|-------------|------|-----------|
| `for_preliminary` | 予選リーグで使用 | `true` |
| `for_final_day` | 最終日（順位リーグ）で使用 | `false` |
| `is_finals_venue` | 決勝トーナメント（3決・決勝）で使用 | `false` |

## データフロー

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Frontend      │      │   Backend       │      │   Database      │
│   (React)       │ ───► │   (FastAPI)     │ ───► │   (SQLite)      │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        │                        │                        │
   Settings.tsx           routes/venues.py          venues テーブル
        │                        │                        │
   snake_case送信     VenueUpdate(Pydantic)      for_final_day
   for_final_day     model_dump() → setattr()    is_finals_venue
```

## フロントエンド（Settings.tsx）

### 会場編集フォーム

```typescript
// フォームの状態
const [venueForm, setVenueForm] = useState({
  name: '',
  address: '',
  groupId: '',
  maxMatchesPerDay: 6,
  forFinalDay: false,      // ← 順位リーグ会場
  isFinalsVenue: false,    // ← 決勝トーナメント会場
})
```

### 保存処理（handleSaveVenue）

```typescript
const handleSaveVenue = () => {
  // snake_caseで明示的に送信
  const payload = {
    id: selectedVenue.id,
    name: venueForm.name,
    address: venueForm.address || null,
    group_id: venueForm.groupId || null,
    max_matches_per_day: venueForm.maxMatchesPerDay,
    for_final_day: venueForm.forFinalDay,      // false も明示的に送信
    is_finals_venue: venueForm.isFinalsVenue,  // false も明示的に送信
  }
  console.log('[handleSaveVenue] Sending payload:', payload)
  updateVenueMutation.mutate(payload)
}
```

### API呼び出し

```typescript
const updateVenueMutation = useMutation({
  mutationFn: async (data) => {
    const { id, ...rest } = data
    console.log('[updateVenueMutation] Sending to API:', rest)
    const response = await api.patch(`/venues/${id}`, rest)
    return response.data
  },
  ...
})
```

## バックエンド（routes/venues.py）

### VenueUpdate スキーマ

```python
class VenueUpdate(CamelCaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    group_id: Optional[str] = None
    max_matches_per_day: Optional[int] = None
    for_preliminary: Optional[bool] = None
    for_final_day: Optional[bool] = None       # ← None = 未送信
    is_finals_venue: Optional[bool] = None     # ← None = 未送信
    ...
```

### CamelCaseModel の設定

```python
class CamelCaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,      # snake_case → camelCase 変換
        populate_by_name=True,         # 両方の形式を受け付ける
        from_attributes=True,
        serialize_by_alias=True,       # レスポンスはcamelCase
    )
```

### 更新処理

```python
@router.patch("/{venue_id}")
def update_venue(venue_id: int, venue_data: VenueUpdate, db: Session):
    venue = db.query(Venue).filter(Venue.id == venue_id).first()

    # 全フィールドを取得（snake_caseで）
    all_data = venue_data.model_dump(by_alias=False)

    # Noneでないフィールドのみ更新
    # False も有効な値として扱われる
    update_data = {}
    for field, value in all_data.items():
        if value is not None:
            update_data[field] = value

    # DBを更新
    for field, value in update_data.items():
        setattr(venue, field, value)

    db.commit()
    return venue
```

## 重要なポイント

### 1. Boolean の false は None と異なる

```python
# false が送信された場合
for_final_day = False
value is not None  # → True → 更新される ✓

# 送信されなかった場合
for_final_day = None
value is not None  # → False → スキップされる ✓
```

### 2. フロントエンドは snake_case で送信

```typescript
// ✓ 正しい
{ for_final_day: false }

// ✗ 以前の問題
{ forFinalDay: false }  // CamelCaseModelで受け取れるはずだが不安定
```

### 3. デバッグログの確認箇所

**フロントエンド（ブラウザコンソール）**:
```
[handleSaveVenue] Sending payload: {for_final_day: false, ...}
[updateVenueMutation] Sending to API: {for_final_day: false, ...}
```

**バックエンド（ターミナル）**:
```
[Venue Update] venue_id=5
[Venue Update] venue_data=name='駒場スタジアム' for_final_day=False ...
[Venue Update] all_data={'name': '駒場スタジアム', 'for_final_day': False, ...}
[Venue Update] update_data={'name': '駒場スタジアム', 'for_final_day': False, ...}
```

## トラブルシューティング

### 問題: チェックを外しても保存されない

1. **ブラウザのNetworkタブ確認**
   - PATCHリクエストのPayloadに `for_final_day: false` があるか
   - レスポンスのステータスが200か

2. **バックエンドログ確認**
   - `update_data` に `'for_final_day': False` が含まれているか

3. **データベース直接確認**
   ```sql
   SELECT id, name, for_final_day, is_finals_venue FROM venues;
   ```

### 問題: camelCase/snake_case の不一致

- フロントエンド: snake_case で送信（推奨）
- バックエンド: CamelCaseModel で両方受け付け可能
- レスポンス: camelCase で返却

## ファイル一覧

| ファイル | 役割 |
|---------|------|
| `src/frontend/src/pages/Settings.tsx` | 会場設定UI |
| `src/backend/routes/venues.py` | 会場API |
| `src/backend/schemas/venue.py` | Pydanticスキーマ |
| `src/backend/models/venue.py` | SQLAlchemyモデル |
