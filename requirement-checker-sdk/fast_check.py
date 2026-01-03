"""
高速要件チェッカー - grepベースの実装
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

PROJECT_ROOT = Path("D:/UrawaCup")
SRC_PATH = PROJECT_ROOT / "src"

class Status(Enum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    NG = "NG"

@dataclass
class CheckItem:
    id: str
    name: str
    phase: str
    patterns: list[str]  # grep patterns
    files: list[str]     # file patterns to check existence

# 要件定義
REQUIREMENTS = [
    # MINI Phase
    CheckItem("MINI-001", "チーム登録機能", "MINI",
              ["class.*Team", "team.*create"],
              ["backend/models/team.py", "backend/routes/teams.py"]),
    CheckItem("MINI-002", "グループ分け機能", "MINI",
              ["group.*assign", "assign.*group"],
              ["backend/routes/teams.py"]),
    CheckItem("MINI-003", "地元/招待区分", "MINI",
              ["TeamType", "is_local"],
              ["backend/models/team.py"]),
    CheckItem("MINI-004", "試合結果入力", "MINI",
              ["class.*Match", "score"],
              ["backend/models/match.py", "backend/routes/matches.py"]),
    CheckItem("MINI-005", "前半/後半/PK得点", "MINI",
              ["first_half", "second_half", "pk_home"],
              ["backend/models/match.py"]),
    CheckItem("MINI-006", "勝点計算", "MINI",
              ["points", "calculate.*standing"],
              ["backend/services/standing_service.py"]),
    CheckItem("MINI-007", "得失点差計算", "MINI",
              ["goal_difference", "goals_for"],
              ["backend/services/standing_service.py"]),
    CheckItem("MINI-008", "H2H順位決定", "MINI",
              ["head_to_head", "h2h", "tiebreak"],
              ["backend/services/standing_service.py"]),
    CheckItem("MINI-009", "CSV/Excelエクスポート", "MINI",
              ["export.*csv", "csv"],
              ["backend/routes/teams.py"]),

    # MIDDLE Phase
    CheckItem("MID-001", "PDF報告書生成", "MIDDLE",
              ["reportlab", "generate.*pdf", "PDF"],
              ["backend/services/report_service.py"]),
    CheckItem("MID-002", "Excel報告書生成", "MIDDLE",
              ["openpyxl", "xlsx"],
              ["backend/services/report_service.py"]),
    CheckItem("MID-003", "会場担当者分散入力", "MIDDLE",
              ["venue.*manager", "VenueManager", "VENUE_STAFF"],
              ["backend/models/user.py", "backend/utils/auth.py"]),
    CheckItem("MID-004", "結果承認フロー", "MIDDLE",
              ["approve", "approval_status", "pending"],
              []),
    CheckItem("MID-005", "対戦除外設定", "MIDDLE",
              ["exclusion", "ExclusionPair"],
              ["backend/models/exclusion_pair.py"]),
    CheckItem("MID-006", "日程自動生成", "MIDDLE",
              ["generate.*schedule", "schedule"],
              ["backend/routes/matches.py"]),
    CheckItem("MID-007", "決勝T自動生成", "MIDDLE",
              ["bracket", "playoff", "knockout", "finals"],
              []),
    CheckItem("MID-008", "権限分離", "MIDDLE",
              ["require_admin", "require_venue", "UserRole"],
              ["backend/utils/auth.py", "backend/models/user.py"]),

    # MAX Phase
    CheckItem("MAX-001", "パブリック閲覧", "MAX",
              ["public.*view", "public.*page", "/public/"],
              []),
    CheckItem("MAX-002", "リアルタイム更新", "MAX",
              ["websocket", "WebSocket", "realtime"],
              []),
    CheckItem("MAX-003", "得点者記録", "MAX",
              ["class.*Goal", "scorer"],
              ["backend/models/goal.py"]),
    CheckItem("MAX-004", "得点ランキング", "MAX",
              ["top.*scorer", "ranking"],
              ["backend/routes/standings.py"]),
    CheckItem("MAX-005", "PWA対応", "MAX",
              ["manifest.json", "service.worker", "serviceWorker"],
              ["frontend/public/manifest.json"]),
    CheckItem("MAX-006", "オフライン同期", "MAX",
              ["offline", "indexeddb", "sync"],
              []),
    CheckItem("MAX-007", "年度別データ", "MAX",
              ["Tournament", "year", "season"],
              ["backend/models/tournament.py"]),

    # Entity
    CheckItem("ENT-001", "Tournamentエンティティ", "ENTITY",
              ["class Tournament"],
              ["backend/models/tournament.py"]),
    CheckItem("ENT-002", "Teamエンティティ", "ENTITY",
              ["class Team"],
              ["backend/models/team.py"]),
    CheckItem("ENT-003", "Playerエンティティ", "ENTITY",
              ["class Player"],
              ["backend/models/player.py"]),
    CheckItem("ENT-004", "Venueエンティティ", "ENTITY",
              ["class Venue"],
              ["backend/models/venue.py"]),
    CheckItem("ENT-005", "Matchエンティティ", "ENTITY",
              ["class Match"],
              ["backend/models/match.py"]),
    CheckItem("ENT-006", "Goalエンティティ", "ENTITY",
              ["class Goal"],
              ["backend/models/goal.py"]),
    CheckItem("ENT-007", "Standingエンティティ", "ENTITY",
              ["class Standing"],
              ["backend/models/standing.py"]),
    CheckItem("ENT-008", "Userエンティティ", "ENTITY",
              ["class User"],
              ["backend/models/user.py"]),
]

def check_file_exists(relative_path: str) -> bool:
    """ファイル存在チェック"""
    full_path = SRC_PATH / relative_path
    return full_path.exists()

def grep_pattern(pattern: str) -> bool:
    """grepでパターン検索（高速）"""
    try:
        # ripgrep使用（インストールされていれば）
        result = subprocess.run(
            ["rg", "-i", "-l", pattern, str(SRC_PATH / "backend")],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0 and result.stdout.strip() != ""
    except FileNotFoundError:
        # ripgrepがない場合はfindstrを使用（Windows）
        try:
            result = subprocess.run(
                ["findstr", "/S", "/I", "/M", pattern, str(SRC_PATH / "backend" / "*.py")],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )
            return result.returncode == 0 and result.stdout.strip() != ""
        except:
            return False
    except:
        return False

def check_requirement(req: CheckItem) -> tuple[Status, list[str]]:
    """要件をチェック"""
    findings = []

    # ファイル存在チェック
    files_found = 0
    for f in req.files:
        if check_file_exists(f):
            files_found += 1
            findings.append(f"File: {f}")

    # パターン検索（ファイルが見つかった場合のみ）
    patterns_found = 0
    if files_found > 0 or not req.files:
        for pattern in req.patterns:
            if grep_pattern(pattern):
                patterns_found += 1
                findings.append(f"Pattern: {pattern}")

    # ステータス判定
    total_checks = len(req.files) + len(req.patterns)
    found_checks = files_found + patterns_found

    if total_checks == 0:
        return Status.NG, ["No check criteria defined"]

    ratio = found_checks / total_checks
    if ratio >= 0.7:
        return Status.OK, findings
    elif ratio >= 0.3:
        return Status.PARTIAL, findings
    else:
        return Status.NG, findings

def main():
    print("=" * 70)
    print("UrawaCup 要件チェック（高速版）")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"プロジェクト: {PROJECT_ROOT}")
    print("=" * 70)

    results = {"MINI": [], "MIDDLE": [], "MAX": [], "ENTITY": []}
    summary = {"MINI": {"OK": 0, "PARTIAL": 0, "NG": 0},
               "MIDDLE": {"OK": 0, "PARTIAL": 0, "NG": 0},
               "MAX": {"OK": 0, "PARTIAL": 0, "NG": 0},
               "ENTITY": {"OK": 0, "PARTIAL": 0, "NG": 0}}

    issues = []

    for req in REQUIREMENTS:
        status, findings = check_requirement(req)
        results[req.phase].append((req, status, findings))
        summary[req.phase][status.value] += 1

        if status != Status.OK:
            issues.append((req, status, findings))

    # フェーズ別サマリー
    print("\n## Phase別サマリー\n")
    print("| Phase | OK | PARTIAL | NG | 実装率 |")
    print("|-------|----|---------|----|--------|")
    for phase in ["MINI", "MIDDLE", "MAX", "ENTITY"]:
        s = summary[phase]
        total = s["OK"] + s["PARTIAL"] + s["NG"]
        rate = (s["OK"] + s["PARTIAL"] * 0.5) / total * 100 if total > 0 else 0
        print(f"| {phase} | {s['OK']} | {s['PARTIAL']} | {s['NG']} | {rate:.0f}% |")

    # 詳細結果
    for phase in ["MINI", "MIDDLE", "MAX", "ENTITY"]:
        print(f"\n### {phase} Phase 詳細\n")
        for req, status, findings in results[phase]:
            icon = {"OK": "[OK]", "PARTIAL": "[--]", "NG": "[NG]"}[status.value]
            print(f"{icon} {req.id}: {req.name}")
            if status != Status.OK and findings:
                for f in findings[:3]:
                    print(f"      {f}")

    # 問題一覧
    if issues:
        print("\n" + "=" * 70)
        print("## 要対応項目（PARTIAL/NG）")
        print("=" * 70)
        for req, status, findings in issues:
            print(f"\n### {req.id}: {req.name} [{status.value}]")
            print(f"- Phase: {req.phase}")
            print(f"- 期待パターン: {req.patterns}")
            print(f"- 期待ファイル: {req.files}")
            if findings:
                print(f"- 検出結果: {findings}")

    print("\n" + "=" * 70)
    print("チェック完了")
    print("=" * 70)

if __name__ == "__main__":
    main()
