# agent-UrawaCup

UrawaCupテスト・調査エージェント集 - Claude Agent SDKを使用

## 概要

このパッケージには、UrawaCupシステムのテスト・調査・修正を自動化する3つのエージェントが含まれています：

| エージェント | 役割 |
|-------------|------|
| **agent_check.py** | ユーザー操作の自動テスト、イシュー記録 |
| **agent_investigate.py** | イシューの調査、原因分析 |
| **agent_fix.py** | 調査結果に基づく自動修正 |

## インストール

```bash
cd D:/UrawaCup/agent-UrawaCup

# Python仮想環境を作成
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 依存関係をインストール
pip install claude-agent-sdk httpx rich
```

---

## agent_check.py - 操作テスト

ユーザー操作が正常に動作するかを自動テストし、問題を `ISSUES.md` に記録します。

### 使用方法

```bash
# 全テスト実行
python agent_check.py

# テスト一覧を表示
python agent_check.py --list

# カテゴリを指定してテスト
python agent_check.py -c venue           # 会場関連のみ
python agent_check.py -c venue match     # 会場と試合関連
python agent_check.py -c infrastructure  # インフラ確認のみ

# 記録されたイシューを表示
python agent_check.py --issues
```

## テストカテゴリ

| カテゴリ | 説明 |
|---------|------|
| `infrastructure` | バックエンド・フロントエンド接続確認 |
| `venue` | 会場関連API・設定保存 |
| `team` | チーム関連API |
| `match` | 試合関連API |
| `build` | フロントエンドビルド確認 |
| `files` | 重要ファイル存在確認 |
| `dragdrop` | ドラッグ&ドロップ機能実装確認 |

## テストシナリオ

| ID | テスト名 | カテゴリ |
|----|---------|---------|
| T001 | バックエンドAPI接続確認 | infrastructure |
| T002 | フロントエンド接続確認 | infrastructure |
| T003 | 会場一覧API確認 | venue |
| T004 | 会場更新API確認（Boolean false送信） | venue |
| T005 | チーム一覧API確認 | team |
| T006 | 試合一覧API確認 | match |
| T007 | フロントエンドビルド確認 | build |
| T008 | 重要ファイル存在確認 | files |
| T009 | createPortal実装確認 | dragdrop |
| T010 | 会場設定snake_case送信確認 | venue |
| T011 | 連打防止実装確認 | dragdrop |

## イシュー記録

テスト中に以下の状況が検出されると、自動的に `ISSUES.md` に記録されます：

- **BUG**: エラーや失敗が発生した場合
- **QUESTION**: 不明点や要調査事項が見つかった場合
- **ERROR**: テスト自体の実行エラー

## 出力例

```
+----------------------------------------+
|       UrawaCup操作テスト開始           |
| テスト数: 11                           |
| イシュー記録先: D:/UrawaCup/ISSUES.md  |
+----------------------------------------+

[OK] バックエンドAPI接続確認
[OK] フロントエンド接続確認
[NG] 会場更新API確認（Boolean false送信）
...

+--------------------------------------+
| PASS: 9 | FAIL: 1 | ERROR: 1         |
| Issues recorded: 2                    |
+--------------------------------------+
```

## 前提条件

- Python 3.10+
- Claude Agent SDK がインストールされていること
- Anthropic API キーが設定されていること（`ANTHROPIC_API_KEY`）
- UrawaCupのバックエンド・フロントエンドが起動していること

---

## agent_investigate.py - イシュー調査

`ISSUES.md` に記録されたイシューを調査し、原因分析レポートを作成します。

### 使用方法

```bash
# 全イシューを調査
python agent_investigate.py

# イシュー一覧を表示
python agent_investigate.py --list

# 特定のイシューを調査
python agent_investigate.py -i T004

# 調査レポート一覧を表示
python agent_investigate.py --reports
```

### 出力先

- `D:/UrawaCup/docs/investigations/` - 調査レポート
- `D:/UrawaCup/docs/investigations/_SUMMARY.md` - サマリー

---

## agent_fix.py - 自動修正

調査レポートを読み取り、実装を要件と比較し、修正可能なものは自動修正します。

### 使用方法

```bash
# 全イシューの修正を試行
python agent_fix.py

# 修正せずに分析のみ（ドライラン）
python agent_fix.py --dry-run

# 特定のイシューを修正
python agent_fix.py -i T004

# 複数のイシューを修正
python agent_fix.py -i T004 T005 T006

# 要件との比較分析を実行
python agent_fix.py --compare

# 調査レポート一覧を表示
python agent_fix.py --list
```

### 出力先

- `D:/UrawaCup/docs/fixes/` - 修正レポート

### 動作フロー

1. `docs/investigations/` の調査レポートを読み込み
2. 各イシューについて分析・修正判断
3. 自動修正可能なものは修正を実行
4. 修正不可能なものは理由を報告
5. 新たな不明点はISSUES.mdに追記

---

## ワークフロー

推奨される使用順序:

```
1. agent_check.py    → テスト実行、イシュー検出
2. agent_investigate.py → イシュー調査、原因分析
3. agent_fix.py      → 自動修正、要件比較
```

---

## 前提条件

- Python 3.10+
- Claude Agent SDK がインストールされていること
- Anthropic API キーが設定されていること（`ANTHROPIC_API_KEY`）
- UrawaCupのバックエンド・フロントエンドが起動していること（agent_check.py）

## ファイル構成

```
agent-UrawaCup/
├── agent_check.py       # 操作テストエージェント
├── agent_investigate.py # イシュー調査エージェント
├── agent_fix.py         # 自動修正エージェント
├── pyproject.toml       # プロジェクト設定
└── README.md            # このファイル

D:/UrawaCup/
├── ISSUES.md                      # イシュー記録
└── docs/
    ├── investigations/            # 調査レポート
    │   ├── _SUMMARY.md
    │   └── T001_*.md, T002_*.md...
    └── fixes/                     # 修正レポート
        └── fix_report_*.md
```
