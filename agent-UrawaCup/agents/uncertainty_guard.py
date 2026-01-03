"""
浦和カップ SDK生成エージェント - 不確実性ガード

推測や思い込みでコードを書くことを防止するエージェント。
不明な点がある場合はIssueを作成し、調査・確認してからコーディングする。
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ISSUE_DIR, LOG_DIR


class UncertaintyType(str, Enum):
    """不確実性の種類"""
    DATA_STRUCTURE = "data_structure"  # データ構造の不明
    API_RESPONSE = "api_response"  # APIレスポンス形式の不明
    TIMING = "timing"  # タイミング・非同期処理の不明
    TYPE_DEFINITION = "type_definition"  # 型定義の不明
    BUSINESS_LOGIC = "business_logic"  # ビジネスロジックの不明
    DEPENDENCY = "dependency"  # 依存関係の不明


@dataclass
class UncertaintyIssue:
    """不確実性Issue"""
    id: int
    type: UncertaintyType
    title: str
    assumption: str  # 推測していた内容
    question: str  # 確認すべき質問
    investigation_steps: List[str]  # 調査手順
    status: str  # "open", "investigating", "clarified", "resolved"
    findings: Optional[str] = None  # 調査結果
    correct_answer: Optional[str] = None  # 正しい答え
    created_at: str = ""
    resolved_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class UncertaintyGuard:
    """
    不確実性ガードクラス

    推測でコードを書く前に立ち止まり、調査を促す。
    """

    def __init__(self):
        self.issues: List[UncertaintyIssue] = []
        self.issue_file = ISSUE_DIR / "UncertaintyIssues.json"
        self.markdown_file = ISSUE_DIR / "UncertaintyIssues.md"
        self._load_issues()

    def _load_issues(self):
        """既存Issueを読み込み"""
        if self.issue_file.exists():
            try:
                data = json.loads(self.issue_file.read_text(encoding="utf-8"))
                self.issues = [
                    UncertaintyIssue(
                        **{**item, "type": UncertaintyType(item["type"])}
                    )
                    for item in data
                ]
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                print(f"Warning: Failed to load uncertainty issues: {e}")
                self.issues = []

    def _save_issues(self):
        """Issueを保存"""
        ISSUE_DIR.mkdir(exist_ok=True)

        # JSON保存
        data = []
        for issue in self.issues:
            d = asdict(issue)
            d["type"] = issue.type.value
            data.append(d)

        self.issue_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # Markdown保存
        self._save_markdown()

    def _save_markdown(self):
        """MarkdownフォーマットでIssue一覧を保存"""
        content = "# 不確実性Issue一覧\n\n"
        content += "**推測でコードを書かない** - 不明な点は調査してから実装する\n\n"
        content += f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Open Issues
        open_issues = [i for i in self.issues if i.status in ("open", "investigating")]
        content += f"## 🔴 未解決の不確実性 ({len(open_issues)})\n\n"

        for issue in open_issues:
            type_emoji = {
                UncertaintyType.DATA_STRUCTURE: "📦",
                UncertaintyType.API_RESPONSE: "🌐",
                UncertaintyType.TIMING: "⏱️",
                UncertaintyType.TYPE_DEFINITION: "📝",
                UncertaintyType.BUSINESS_LOGIC: "💼",
                UncertaintyType.DEPENDENCY: "🔗",
            }.get(issue.type, "❓")

            content += f"### {type_emoji} Issue #{issue.id:03d}: {issue.title}\n\n"
            content += f"**種類**: {issue.type.value}\n"
            content += f"**ステータス**: {issue.status}\n\n"
            content += f"#### ❌ 推測していた内容\n"
            content += f"> {issue.assumption}\n\n"
            content += f"#### ❓ 確認すべき質問\n"
            content += f"> {issue.question}\n\n"
            content += f"#### 📋 調査手順\n"
            for i, step in enumerate(issue.investigation_steps, 1):
                content += f"{i}. {step}\n"
            content += "\n"

            if issue.findings:
                content += f"#### 🔍 調査結果\n"
                content += f"{issue.findings}\n\n"

        # Resolved Issues
        resolved = [i for i in self.issues if i.status in ("clarified", "resolved")]
        content += f"\n## ✅ 解決済み ({len(resolved)})\n\n"

        for issue in resolved:
            content += f"### Issue #{issue.id:03d}: {issue.title}\n\n"
            content += f"**推測**: {issue.assumption}\n\n"
            content += f"**正解**: {issue.correct_answer or issue.findings}\n\n"
            content += "---\n\n"

        self.markdown_file.write_text(content, encoding="utf-8")

    def check_data_structure(
        self,
        context: str,
        expected_structure: str,
        source: str,
    ) -> Optional[UncertaintyIssue]:
        """
        データ構造の推測をチェック

        Args:
            context: コンテキスト（何をしようとしているか）
            expected_structure: 期待しているデータ構造
            source: データの出所（APIなど）

        Returns:
            不確実性がある場合はIssueを返す
        """
        return self.create_issue(
            type=UncertaintyType.DATA_STRUCTURE,
            title=f"データ構造の確認: {context}",
            assumption=f"「{source}」は「{expected_structure}」形式で返ってくるはずだ",
            question=f"実際に「{source}」はどのような形式でデータを返すのか？",
            investigation_steps=[
                f"console.log() で {source} のレスポンスを確認する",
                "バックエンドのAPIエンドポイント定義を確認する",
                "型定義ファイル（schemas/）を確認する",
                "実際に返ってくるJSONの構造をメモする",
            ],
        )

    def check_api_response(
        self,
        endpoint: str,
        expected_type: str,
        method: str = "GET",
    ) -> Optional[UncertaintyIssue]:
        """
        APIレスポンス形式の推測をチェック

        Args:
            endpoint: APIエンドポイント
            expected_type: 期待している型
            method: HTTPメソッド
        """
        return self.create_issue(
            type=UncertaintyType.API_RESPONSE,
            title=f"APIレスポンス確認: {method} {endpoint}",
            assumption=f"APIは「{expected_type}」を直接返すはずだ",
            question=f"{method} {endpoint} の実際のレスポンス形式は？配列？オブジェクト？ラップされている？",
            investigation_steps=[
                f"バックエンドの routes/ ファイルで {endpoint} を検索する",
                "response_model を確認して実際の返却型を特定する",
                "schemas/ の該当する型定義を確認する",
                "Thunder ClientやPostmanでAPIを叩いて実際のレスポンスを確認する",
                "フロントエンドで使う前に console.log(response) で中身を見る",
            ],
        )

    def check_timing(
        self,
        operation: str,
        assumption: str,
    ) -> Optional[UncertaintyIssue]:
        """
        タイミング・非同期処理の推測をチェック

        Args:
            operation: 操作内容
            assumption: タイミングに関する推測
        """
        return self.create_issue(
            type=UncertaintyType.TIMING,
            title=f"タイミング確認: {operation}",
            assumption=assumption,
            question="データが利用可能になるタイミングはいつか？ガード処理は必要か？",
            investigation_steps=[
                "useQueryのisLoading, isError状態を確認する",
                "初期値（undefined/null/空配列）を適切に設定しているか確認する",
                "データがない場合のフォールバック表示を実装しているか確認する",
                "Optional chaining (?.) を使用しているか確認する",
                "早期リターン（if (!data) return ...）を実装しているか確認する",
            ],
        )

    def create_issue(
        self,
        type: UncertaintyType,
        title: str,
        assumption: str,
        question: str,
        investigation_steps: List[str],
    ) -> UncertaintyIssue:
        """不確実性Issueを作成"""
        issue_id = max((i.id for i in self.issues), default=0) + 1

        issue = UncertaintyIssue(
            id=issue_id,
            type=type,
            title=title,
            assumption=assumption,
            question=question,
            investigation_steps=investigation_steps,
            status="open",
        )

        self.issues.append(issue)
        self._save_issues()

        print(f"\n{'='*60}")
        print(f"⚠️  不確実性を検出しました - Issue #{issue_id}")
        print(f"{'='*60}")
        print(f"推測: {assumption}")
        print(f"質問: {question}")
        print(f"\n調査手順:")
        for i, step in enumerate(investigation_steps, 1):
            print(f"  {i}. {step}")
        print(f"{'='*60}\n")

        return issue

    def record_findings(
        self,
        issue_id: int,
        findings: str,
        correct_answer: Optional[str] = None,
    ):
        """調査結果を記録"""
        for issue in self.issues:
            if issue.id == issue_id:
                issue.findings = findings
                issue.correct_answer = correct_answer
                issue.status = "clarified"
                break
        self._save_issues()

    def resolve_issue(self, issue_id: int, correct_answer: str):
        """Issueを解決済みにする"""
        for issue in self.issues:
            if issue.id == issue_id:
                issue.correct_answer = correct_answer
                issue.status = "resolved"
                issue.resolved_at = datetime.now().isoformat()
                break
        self._save_issues()

    def get_open_issues(self) -> List[UncertaintyIssue]:
        """未解決のIssueを取得"""
        return [i for i in self.issues if i.status in ("open", "investigating")]

    def must_investigate_before_coding(self) -> bool:
        """
        コーディング前に調査が必要かどうか

        Open Issueがある場合はTrueを返す
        """
        open_issues = self.get_open_issues()
        if open_issues:
            print("\n" + "="*60)
            print("🛑 コーディングを停止してください！")
            print("="*60)
            print(f"未解決の不確実性が {len(open_issues)} 件あります。")
            print("先に調査を完了してからコーディングしてください。\n")
            for issue in open_issues:
                print(f"  - Issue #{issue.id}: {issue.title}")
            print("\n調査結果を記録するには:")
            print("  guard.record_findings(issue_id, '調査結果')")
            print("  guard.resolve_issue(issue_id, '正しい答え')")
            print("="*60 + "\n")
            return True
        return False


# 推測パターンの検出
ASSUMPTION_PATTERNS = [
    # データ構造の推測
    (r"\.map\s*\(", "配列に対して.map()を使用", UncertaintyType.DATA_STRUCTURE),
    (r"data\s*\?\.\s*\w+", "オプショナルチェーンでデータアクセス", UncertaintyType.DATA_STRUCTURE),
    (r"response\.data", "レスポンスから直接dataを取得", UncertaintyType.API_RESPONSE),

    # 初期値の推測
    (r"=\s*\[\]", "空配列で初期化", UncertaintyType.DATA_STRUCTURE),
    (r"=\s*\{\}", "空オブジェクトで初期化", UncertaintyType.DATA_STRUCTURE),

    # 型の推測
    (r"as\s+\w+\[\]", "配列型としてキャスト", UncertaintyType.TYPE_DEFINITION),
    (r"<\w+\[\]>", "配列型を期待", UncertaintyType.TYPE_DEFINITION),
]


def analyze_code_for_assumptions(code: str) -> List[Dict[str, Any]]:
    """
    コード内の推測パターンを分析

    Args:
        code: 分析対象のコード

    Returns:
        検出された推測パターンのリスト
    """
    findings = []

    for pattern, description, uncertainty_type in ASSUMPTION_PATTERNS:
        matches = re.finditer(pattern, code)
        for match in matches:
            # マッチした行を取得
            start = code.rfind("\n", 0, match.start()) + 1
            end = code.find("\n", match.end())
            if end == -1:
                end = len(code)
            line = code[start:end].strip()

            findings.append({
                "pattern": pattern,
                "description": description,
                "type": uncertainty_type,
                "matched_text": match.group(),
                "line": line,
                "position": match.start(),
            })

    return findings


# グローバルインスタンス
uncertainty_guard = UncertaintyGuard()


if __name__ == "__main__":
    # テスト
    guard = UncertaintyGuard()

    # APIレスポンスの不確実性をチェック
    issue = guard.check_api_response(
        endpoint="/api/venues",
        expected_type="Venue[]",
        method="GET",
    )

    # データ構造の不確実性をチェック
    issue2 = guard.check_data_structure(
        context="会場一覧の表示",
        expected_structure="配列（Venue[]）",
        source="GET /api/venues",
    )

    # コーディング前のチェック
    if guard.must_investigate_before_coding():
        print("調査を完了してからコーディングを再開してください。")
    else:
        print("調査完了！コーディングを開始できます。")
