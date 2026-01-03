# UrawaCup 要件チェックSDK

浦和カップシステムの要件定義（`Requirement_Phased.md`、`requirement.md`）に基づいて、実装状況を自動チェックするツールです。

## 機能

- **要件の構造化管理**: フェーズ別（MINI/MIDDLE/MAX）、優先度別、カテゴリ別に要件を管理
- **実装状況の自動チェック**: コードベースを検索し、各要件の実装状況を判定
- **レポート生成**: Markdown形式の詳細レポートを自動生成
- **Issue出力**: 未実装・問題のある要件をIssue形式で出力

## 使用方法

### フルチェック実行

```bash
python main.py
```

### フェーズ別チェック

```bash
# MINI フェーズのみチェック
python main.py --phase MINI

# MIDDLE フェーズのみチェック
python main.py --phase MIDDLE

# MAX フェーズのみチェック
python main.py --phase MAX
```

### 優先度別チェック

```bash
# 最高優先度のみチェック
python main.py --priority 最高

# 高優先度のみチェック
python main.py --priority 高
```

### レポート生成

```bash
# フルチェック + レポート生成
python main.py --report

# Issue一覧も出力
python main.py --report --issues
```

### バッチファイルで実行

```bash
# Windows
run_check.bat

# Phase MINI のみ
run_phase_mini.bat
```

## ディレクトリ構成

```
requirement-checker-sdk/
├── main.py                 # メイン実行スクリプト
├── run_check.bat           # フルチェック実行バッチ
├── run_phase_mini.bat      # MINI フェーズチェック
├── requirements.txt        # 依存パッケージ
├── README.md               # このファイル
├── reports/                # 生成されたレポート
│   └── requirement_check_*.md
└── src/
    ├── __init__.py
    ├── requirements_data.py  # 要件定義（構造化データ）
    └── code_checker.py       # コードチェッカー
```

## 要件定義

### フェーズ別要件数

| フェーズ | 概要 | 要件数 |
|----------|------|--------|
| MINI | 信頼できる計算機 | 9 |
| MIDDLE | 業務効率化ツール | 8 |
| MAX | 大会プラットフォーム | 7 |
| エンティティ | データモデル | 8 |

### 優先度レベル

- **最高**: 報告書生成、試合結果入力、順位計算
- **高**: チーム管理、会場管理、得点記録
- **中**: 日程生成、オフライン対応、選手管理
- **低**: アーカイブ機能

## 実装ステータス

- **完了**: パターンマッチ率 80% 以上
- **部分実装**: パターンマッチ率 50-79%
- **実装中**: パターンマッチ率 1-49%
- **未着手**: パターンマッチ率 0%

## プログラムから使用する

```python
from requirement_checker_sdk.main import RequirementChecker
from requirement_checker_sdk.src.requirements_data import Phase

# チェッカーを初期化
checker = RequirementChecker("D:/UrawaCup")

# フルチェック
result = checker.run_full_check()

# フェーズ別チェック
mini_result = checker.run_phase_check(Phase.MINI)

# レポート生成
report_path = checker.generate_report()

# 未実装要件を取得
not_implemented = checker.get_not_implemented()
for item in not_implemented:
    print(f"{item.requirement.id}: {item.requirement.name}")
```

## Claude Agent SDKとの連携

将来的にClaude Agent SDKを使用して、より高度な自動チェックを実現できます：

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def check_with_agent():
    options = ClaudeAgentOptions(
        system_prompt="あなたは浦和カップシステムの要件チェッカーです。",
        allowed_tools=["Read", "Glob", "Grep"],
        cwd="D:/UrawaCup"
    )

    async for message in query(
        prompt="src/backendのコードを分析し、MINI要件の実装状況を確認してください",
        options=options
    ):
        print(message)
```
