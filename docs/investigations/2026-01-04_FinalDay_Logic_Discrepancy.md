# 最終日ロジック 要件・実装不一致調査レポート

**調査日**: 2026-01-04
**調査者**: Claude Code
**対象**: 最終日の決勝トーナメント・研修試合ロジック

---

## 1. 発見された不一致

### 1.1 決勝トーナメント組み合わせ

| 項目 | 最新要件 | 実装 |
|------|---------|------|
| 準決勝1 | A1位 vs **C1位** | A1位 vs **B1位** |
| 準決勝2 | **B1位** vs D1位 | **C1位** vs D1位 |

### 1.2 研修試合（順位リーグ）

| 項目 | 最新要件 | 実装 |
|------|---------|------|
| 構造 | **4つの順位リーグ**（全体順位でソート→リーグ振り分け→総当たり） | 同順位ペアリング（2位同士、3位同士...） |
| 試合数 | リーグ内総当たり（5チーム→10試合） | 同順位ペア×異なるグループのみ |

---

## 2. 不一致の原因

### 2.1 要件書の変遷

**準決勝の組み合わせ**に関する要件書の履歴:

| ファイル | 内容 | 時期 |
|----------|------|------|
| `Requirement/old/RequirementSpecification.md:517-518` | A1 vs B1, C1 vs D1 | 初期 |
| `Requirement/old/requirement.md:64` | A1 vs B1, C1 vs D1（基本形） | 初期 |
| `Requirement/new/FinalDay_Logic_Final.md:15-16` | **A1 vs C1, B1 vs D1** | **最新** |

### 2.2 実装時の参照元

実装 (`src/backend/routes/matches.py:995-1042`) は、**古い要件書 (RequirementSpecification.md)** に基づいて作成された。

```python
# matches.py:1007-1019 (現在の実装)
# 準決勝1: A1位 vs B1位
semifinal1 = Match(
    home_team_id=qualified_teams["A"],
    away_team_id=qualified_teams["B"],  # ← 古い要件に基づく
    ...
)
# 準決勝2: C1位 vs D1位
semifinal2 = Match(
    home_team_id=qualified_teams["C"],  # ← 古い要件に基づく
    away_team_id=qualified_teams["D"],
    ...
)
```

### 2.3 要件更新後の実装未反映

- 要件書が `FinalDay_Logic_Final.md` で更新された
- 更新内容:
  - 準決勝の組み合わせ変更（A-C, B-D）
  - 研修試合を「順位リーグ」形式に変更
- **実装への反映が漏れた**

---

## 3. 要件変更の背景（推測）

### 3.1 準決勝の組み合わせ変更理由

**A-B, C-D 方式（旧）:**
- 隣接グループ同士の対戦

**A-C, B-D 方式（新）:**
- 対角グループ同士の対戦
- 決勝でA-B間、C-D間のチームが対戦する可能性
- より多様な対戦カードを実現

### 3.2 研修試合の構造変更理由

**同順位ペアリング方式（旧・実装）:**
- 単純な同順位同士のマッチング
- 予選未対戦チェックによりスキップが発生
- 試合数が不均等になる可能性

**順位リーグ方式（新・要件）:**
- 全体順位でグループ化し、リーグ内総当たり
- 試合数が明確（5チーム→10試合、4チーム→6試合）
- 全チームが同じ回数試合できる

---

## 4. 影響範囲

### 4.1 バックエンド

| ファイル | 影響 |
|----------|------|
| `src/backend/routes/matches.py` | `generate_final_matches()` の組み合わせロジック修正 |
| `src/backend/routes/matches.py` | `generate_training_matches()` の全面的な再設計 |
| `src/backend/services/standing_service.py` | 全体順位計算ロジックの追加 |

### 4.2 フロントエンド

| ファイル | 影響 |
|----------|------|
| `src/frontend/src/pages/FinalDaySchedule.tsx` | 順位リーグUI表示の実装 |
| `src/frontend/src/components/FinalsBracket.tsx` | 組み合わせ表示の確認 |

---

## 5. 修正方針

### 5.1 即時修正（低リスク） ✅ 完了

1. **準決勝の組み合わせ修正** ✅
   - `matches.py:1007-1042` の `qualified_teams["B"]` と `qualified_teams["C"]` を入れ替え
   - 影響: 小（コード2行の変更）
   - **修正日**: 2026-01-04
   - **修正内容**:
     - 準決勝1: A1位 vs B1位 → A1位 vs C1位
     - 準決勝2: C1位 vs D1位 → B1位 vs D1位
     - 3位決定戦・決勝のプレースホルダーも更新

### 5.2 中期修正（要設計） ✅ 完了

2. **研修試合（順位リーグ）の再設計** ✅
   - 全体順位計算ロジックの実装
   - リーグ振り分けロジックの実装
   - 総当たり対戦表生成の実装
   - 影響: 大（新規機能に近い）
   - **修正日**: 2026-01-04
   - **修正内容**:
     - `StandingService.calculate_overall_standings()` 追加
     - `StandingService.get_position_league_teams()` 追加
     - `generate_training_matches()` 完全書き換え
     - 再戦チェック機能追加
     - 警告システム（ランダム決定、チーム数不均等）追加

---

## 6. 教訓・再発防止

### 6.1 発生した問題

- 要件書が更新されたが、実装チームへの伝達が不十分だった
- 要件書の `old/` と `new/` の区分が曖昧だった

### 6.2 再発防止策

1. **要件変更時のチェックリスト作成**
   - 影響する実装箇所の特定
   - 実装担当者への通知

2. **要件書のバージョン管理強化**
   - 変更履歴の明記
   - 古い要件書への「DEPRECATED」マーク

3. **定期的な要件・実装照合**
   - 主要機能の要件照合を定期実施

---

## 7. 関連ファイル

### 要件書
- `Requirement/new/FinalDay_Logic_Final.md` ← **最新・正**
- `Requirement/FinalDay_Screen_Detailed_Spec.md`
- `Requirement/old/RequirementSpecification.md` ← 古い（実装の参照元）

### 実装
- `src/backend/routes/matches.py`
- `src/backend/services/standing_service.py`
- `src/frontend/src/components/FinalsBracket.tsx`

---

# Report PDF 要件・実装照合

**調査日**: 2026-01-04
**対象**: Report_PDF_Specification.md

## 1. API エンドポイントの差分

| 要件 | 実装 | 状態 |
|------|------|------|
| `POST /tournaments/{id}/reports/daily` | `GET /export/pdf` | ⚠️ パス・メソッド異なる |
| `POST /tournaments/{id}/reports/final` | `GET /export/final-result` | ⚠️ パス・メソッド異なる |
| `GET /tournaments/{id}/report-settings` | `GET /sender-settings/{id}` | ⚠️ パス異なる |
| `PUT /tournaments/{id}/report-settings` | `PATCH /sender-settings/{id}` | ⚠️ パス・メソッド異なる |

## 2. 機能の差分

| 機能 | 要件 | 実装 | 状態 |
|------|------|------|------|
| 日別試合結果PDF | ✅ | ✅ ReportService.generate_pdf | ✅ |
| 最終結果PDF | ✅ | ✅ FinalResultReportGenerator | ✅ |
| 得点経過表示 | ✅ 時間+チーム名 | ✅ GoalReport | ✅ |
| PK戦表示 | ✅ | ✅ score_pk | ✅ |
| 会場別ブロック | ✅ | ✅ | ✅ |
| 送信先・発信元ヘッダー | ✅ | ✅ sender_settings | ✅ |
| 研修試合結果（最終結果） | ✅ 会場別表示 | ⚠️ 要確認 | ⚠️ |
| 優秀選手（最終結果） | ✅ MVP+優秀選手 | ⚠️ 要確認 | ⚠️ |
| プレビュー機能 | ✅ | ❌ 未実装 | ❌ |
| 未入力警告表示 | ✅ | ❌ 未実装 | ❌ |

## 3. 不一致の原因

### 3.1 APIパス設計の差異

**要件書の設計思想:**
- RESTful な階層構造 `/tournaments/{id}/reports/...`
- リソース中心のURL設計
- HTTPメソッドで操作を表現（POST=生成、GET=取得、PUT=更新）

**実装時の判断:**
- 機能中心のURL設計 `/reports/export/...`
- クエリパラメータで柔軟にフィルタリング
- 実装の簡便さを優先

**なぜこの差異が発生したか:**
1. **要件書の作成時期と実装時期のズレ**
   - 要件書は理想的なRESTful設計で記述
   - 実装時に既存のAPIパターン（`/reports/...`）に合わせた
2. **既存コードとの整合性**
   - 他のエクスポート機能が `/export/...` パターンを使用
   - 一貫性のため同じパターンを採用
3. **フロントエンドとの調整不足**
   - バックエンド実装者が独自に判断
   - 要件書との照合が行われなかった

### 3.2 未実装機能の原因

**プレビュー機能が未実装の理由:**
1. **優先度の判断**
   - 基本的なPDF生成が優先された
   - プレビューは「あれば便利」な機能として後回し
2. **技術的な課題**
   - PDFのリアルタイムプレビューは実装コストが高い
   - Base64エンコードしてiframeで表示する方式が必要
3. **時間的制約**
   - 初期リリースに間に合わせるため省略

**未入力警告表示が未実装の理由:**
1. **データ検証ロジックの複雑さ**
   - どのフィールドが「未入力」かの定義が曖昧
   - 試合結果、得点者、審判など多岐にわたる
2. **要件の詳細不足**
   - 要件書に警告の具体的な条件が記載されていない
   - 実装者が判断を保留

### 3.3 根本原因

| 原因 | 詳細 |
|------|------|
| **要件書の参照不足** | 実装時に要件書を十分に参照しなかった |
| **レビュープロセスの欠如** | 要件との照合レビューが行われなかった |
| **優先度の暗黙的判断** | 一部機能を「後で実装」として暗黙的にスキップ |
| **コミュニケーション不足** | 要件作成者と実装者間の認識合わせが不十分 |

---

## 4. 影響度

- **低**: APIパスの差異は内部利用のみなので影響は軽微
- **中**: プレビュー機能・未入力警告はUX向上に有用だが必須ではない
- **要確認**: 研修試合結果・優秀選手の出力内容が要件通りか

---

## 5. 修正方針

### 5.1 APIパスの統一（低優先度） ✅ 完了

**修正日**: 2026-01-04
**実装内容**:
- 要件準拠のAPIパスを追加
- レガシーAPIは後方互換性のため維持（`include_in_schema=False`）

| 機能 | 要件 | 新しい実装パス |
|------|------|---------------|
| 日別PDF | `POST /tournaments/{id}/reports/daily` | `POST /api/reports/tournaments/{id}/daily` |
| 最終結果PDF | `POST /tournaments/{id}/reports/final` | `POST /api/reports/tournaments/{id}/final` |
| 設定取得 | `GET /tournaments/{id}/report-settings` | `GET /api/reports/tournaments/{id}/report-settings` |
| 設定更新 | `PUT /tournaments/{id}/report-settings` | `PUT /api/reports/tournaments/{id}/report-settings` |

### 5.2 未実装機能の追加（中優先度） ✅ 完了

**プレビュー機能:** ✅
- 実装コスト: 中
- 方式: PDFをBase64エンコードしてフロントエンドでiframe表示
- 対象ファイル: `src/backend/routes/reports.py`
- **修正日**: 2026-01-04
- **実装内容**:
  - `GET /api/reports/preview/pdf` - 日別報告書プレビュー
  - `GET /api/reports/preview/final-result` - 最終結果プレビュー
  - Base64エンコードしてJSONで返却

**未入力警告:** ✅
- 実装コスト: 中
- 必要な定義: 「未入力」の具体的な条件を明確化
- 対象ファイル: `src/backend/routes/reports.py`
- **修正日**: 2026-01-04
- **実装内容**:
  - `GET /api/reports/check-incomplete` - 未入力チェックAPI
  - 日別報告書: 試合結果未入力、スコア不完全、得点経過未入力
  - 最終結果: 決勝T結果未入力、MVP未登録、優秀選手不足
  - `warnings`（軽微）と`critical_warnings`（致命的）を区別
  - `can_export`フラグで出力可否を判定

---

## 6. 教訓（Report PDF）

### 6.1 発生した問題

- 要件書と実装で異なるAPI設計思想が採用された
- 「あれば便利」な機能が暗黙的にスキップされた
- 要件書の詳細度が不足していた箇所があった

### 6.2 再発防止策

1. **API設計レビューの実施**
   - 実装前にAPIパス設計を要件と照合
   - 変更する場合は理由を文書化

2. **機能優先度の明示化**
   - 要件書に優先度（Must/Should/Could）を明記
   - スキップする機能は明示的に決定・記録

3. **要件書の詳細化**
   - 「警告表示」などの機能は具体的な条件を記載
   - 実装者が判断に迷わないレベルまで詳細化
