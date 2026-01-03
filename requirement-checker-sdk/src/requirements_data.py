"""
浦和カップシステム要件定義（構造化データ）
Requirement_Phased.md と requirement.md を基に構造化
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Phase(Enum):
    MINI = "MINI"
    MIDDLE = "MIDDLE"
    MAX = "MAX"


class Priority(Enum):
    HIGHEST = "最高"
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


class ImplementationStatus(Enum):
    NOT_STARTED = "未着手"
    IN_PROGRESS = "実装中"
    COMPLETED = "完了"
    PARTIAL = "部分実装"


@dataclass
class Requirement:
    """要件を表すデータクラス"""
    id: str
    name: str
    description: str
    phase: Phase
    priority: Priority
    category: str
    check_patterns: list[str] = field(default_factory=list)  # コード内検索パターン
    check_files: list[str] = field(default_factory=list)  # チェック対象ファイルパターン
    status: ImplementationStatus = ImplementationStatus.NOT_STARTED
    notes: str = ""


# =============================================================================
# Phase 1: MINI - 信頼できる計算機
# =============================================================================
MINI_REQUIREMENTS = [
    # チーム・グループ管理
    Requirement(
        id="MINI-001",
        name="チーム登録機能",
        description="24チームの登録・編集・削除機能",
        phase=Phase.MINI,
        priority=Priority.HIGH,
        category="チーム・グループ管理",
        check_patterns=[
            r"class.*Team",
            r"team.*create",
            r"team.*register",
            r"/teams",
        ],
        check_files=["**/team*.py", "**/team*.ts", "**/Team*.tsx"]
    ),
    Requirement(
        id="MINI-002",
        name="グループ分け機能",
        description="4グループ（A〜D）へのチーム割り当て",
        phase=Phase.MINI,
        priority=Priority.HIGH,
        category="チーム・グループ管理",
        check_patterns=[
            r"class.*Group",
            r"group.*assign",
            r"GroupA|GroupB|GroupC|GroupD",
        ],
        check_files=["**/group*.py", "**/group*.ts"]
    ),
    Requirement(
        id="MINI-003",
        name="地元/招待区分設定",
        description="チームの地元/招待区分の設定",
        phase=Phase.MINI,
        priority=Priority.HIGH,
        category="チーム・グループ管理",
        check_patterns=[
            r"is_local|isLocal|team_type|TeamType",
            r"local.*team|invited.*team",
        ],
        check_files=["**/team*.py", "**/team*.ts"]
    ),

    # 試合結果入力
    Requirement(
        id="MINI-004",
        name="試合結果入力（管理者のみ）",
        description="固定日程に対するスコア入力機能",
        phase=Phase.MINI,
        priority=Priority.HIGHEST,
        category="試合結果管理",
        check_patterns=[
            r"class.*Match",
            r"score.*input|input.*score",
            r"home_score|away_score|homeScore|awayScore",
        ],
        check_files=["**/match*.py", "**/match*.ts", "**/MatchResult*.tsx"]
    ),
    Requirement(
        id="MINI-005",
        name="スコア（前半・後半・合計・PK）入力",
        description="詳細スコアの入力",
        phase=Phase.MINI,
        priority=Priority.HIGHEST,
        category="試合結果管理",
        check_patterns=[
            r"first_half|second_half|firstHalf|secondHalf",
            r"pk_score|pkScore|penalty",
        ],
        check_files=["**/match*.py", "**/match*.ts"]
    ),

    # 順位表自動計算
    Requirement(
        id="MINI-006",
        name="勝点計算",
        description="勝利=3点、引分=1点、敗北=0点の自動計算",
        phase=Phase.MINI,
        priority=Priority.HIGHEST,
        category="順位表計算",
        check_patterns=[
            r"points|勝点|win.*3|victory.*3",
            r"calculate.*standing|standing.*calculate",
        ],
        check_files=["**/standing*.py", "**/standing*.ts", "**/Standings*.tsx"]
    ),
    Requirement(
        id="MINI-007",
        name="得失点差計算",
        description="総得点 - 総失点の自動計算",
        phase=Phase.MINI,
        priority=Priority.HIGHEST,
        category="順位表計算",
        check_patterns=[
            r"goal_difference|goalDifference|得失点",
            r"goals_for.*goals_against|goalsFor.*goalsAgainst",
        ],
        check_files=["**/standing*.py", "**/standing*.ts"]
    ),
    Requirement(
        id="MINI-008",
        name="対戦成績（H2H）による順位決定",
        description="同勝点時の直接対決成績での順位決定",
        phase=Phase.MINI,
        priority=Priority.HIGH,
        category="順位表計算",
        check_patterns=[
            r"head_to_head|h2h|直接対決",
            r"tiebreaker|同点|同勝点",
        ],
        check_files=["**/standing*.py", "**/ranking*.py"]
    ),

    # 基礎エクスポート
    Requirement(
        id="MINI-009",
        name="CSV/Excelエクスポート",
        description="データ確認用のCSV/Excel出力",
        phase=Phase.MINI,
        priority=Priority.MEDIUM,
        category="エクスポート",
        check_patterns=[
            r"export.*csv|csv.*export",
            r"export.*excel|excel.*export",
            r"\.csv|\.xlsx",
        ],
        check_files=["**/export*.py", "**/report*.py"]
    ),
]

# =============================================================================
# Phase 2: MIDDLE - 業務効率化ツール
# =============================================================================
MIDDLE_REQUIREMENTS = [
    # 公式帳票出力
    Requirement(
        id="MID-001",
        name="PDF報告書生成",
        description="埼玉新聞、TV埼玉など提出先ごとのフォーマットでのPDF出力",
        phase=Phase.MIDDLE,
        priority=Priority.HIGHEST,
        category="報告書生成",
        check_patterns=[
            r"pdf.*generate|generate.*pdf",
            r"reportlab|weasyprint|pdf",
            r"報告書|report",
        ],
        check_files=["**/report*.py", "**/pdf*.py", "**/Reports*.tsx"]
    ),
    Requirement(
        id="MID-002",
        name="Excel報告書生成",
        description="既存フォーマット踏襲のExcel出力",
        phase=Phase.MIDDLE,
        priority=Priority.HIGHEST,
        category="報告書生成",
        check_patterns=[
            r"openpyxl|xlsxwriter|excel",
            r"\.xlsx",
        ],
        check_files=["**/report*.py", "**/excel*.py"]
    ),

    # 分散入力対応
    Requirement(
        id="MID-003",
        name="会場担当者による分散入力",
        description="各会場の担当者がスマホ/タブレットで入力",
        phase=Phase.MIDDLE,
        priority=Priority.HIGH,
        category="分散入力",
        check_patterns=[
            r"venue.*manager|会場.*担当",
            r"role.*venue|VenueManager",
        ],
        check_files=["**/user*.py", "**/auth*.py", "**/venue*.py"]
    ),
    Requirement(
        id="MID-004",
        name="結果承認フロー",
        description="会場入力→本部承認のワークフロー",
        phase=Phase.MIDDLE,
        priority=Priority.HIGH,
        category="分散入力",
        check_patterns=[
            r"approve|承認|confirm",
            r"pending.*approval|status.*pending",
        ],
        check_files=["**/match*.py", "**/approval*.py"]
    ),

    # 日程調整
    Requirement(
        id="MID-005",
        name="対戦除外設定",
        description="対戦禁止カードのバリデーション機能",
        phase=Phase.MIDDLE,
        priority=Priority.HIGH,
        category="日程管理",
        check_patterns=[
            r"exclusion|exclude|対戦除外",
            r"cannot.*play|禁止",
        ],
        check_files=["**/exclusion*.py", "**/schedule*.py"]
    ),
    Requirement(
        id="MID-006",
        name="日程自動生成",
        description="対戦除外設定に基づく試合日程の自動生成",
        phase=Phase.MIDDLE,
        priority=Priority.MEDIUM,
        category="日程管理",
        check_patterns=[
            r"schedule.*generate|generate.*schedule",
            r"日程.*生成|auto.*schedule",
        ],
        check_files=["**/schedule*.py", "**/MatchSchedule*.tsx"]
    ),

    # 決勝トーナメント
    Requirement(
        id="MID-007",
        name="決勝Tマッチング自動生成",
        description="予選順位に基づく決勝トーナメントの枠自動埋め",
        phase=Phase.MIDDLE,
        priority=Priority.MEDIUM,
        category="決勝トーナメント",
        check_patterns=[
            r"tournament.*bracket|bracket",
            r"playoff|決勝|knockout",
        ],
        check_files=["**/tournament*.py", "**/bracket*.py"]
    ),

    # 権限分離
    Requirement(
        id="MID-008",
        name="Admin/VenueManager権限分離",
        description="管理者と会場担当者の権限分離",
        phase=Phase.MIDDLE,
        priority=Priority.HIGH,
        category="認証・権限",
        check_patterns=[
            r"role|permission|権限",
            r"admin|administrator|管理者",
            r"venue.*manager|会場.*担当",
        ],
        check_files=["**/user*.py", "**/auth*.py", "**/role*.py"]
    ),
]

# =============================================================================
# Phase 3: MAX - 大会プラットフォーム
# =============================================================================
MAX_REQUIREMENTS = [
    # パブリックビューイング
    Requirement(
        id="MAX-001",
        name="パブリック閲覧サイト",
        description="ログイン不要の閲覧専用サイト",
        phase=Phase.MAX,
        priority=Priority.HIGH,
        category="パブリック機能",
        check_patterns=[
            r"public.*view|public.*page",
            r"guest|anonymous",
        ],
        check_files=["**/public*.py", "**/public*.tsx"]
    ),
    Requirement(
        id="MAX-002",
        name="リアルタイム更新",
        description="試合結果のリアルタイム確認機能",
        phase=Phase.MAX,
        priority=Priority.MEDIUM,
        category="パブリック機能",
        check_patterns=[
            r"websocket|realtime|real-time",
            r"socket\.io|sse|server-sent",
        ],
        check_files=["**/websocket*.py", "**/realtime*.py"]
    ),

    # 詳細スタッツ
    Requirement(
        id="MAX-003",
        name="得点者記録",
        description="「誰が、いつ決めたか」の詳細記録",
        phase=Phase.MAX,
        priority=Priority.MEDIUM,
        category="詳細スタッツ",
        check_patterns=[
            r"class.*Goal",
            r"scorer|得点者|goal_time",
        ],
        check_files=["**/goal*.py", "**/goal*.ts"]
    ),
    Requirement(
        id="MAX-004",
        name="得点ランキング",
        description="得点ランキングの自動生成",
        phase=Phase.MAX,
        priority=Priority.MEDIUM,
        category="詳細スタッツ",
        check_patterns=[
            r"ranking|ランキング|top.*scorer",
            r"goal.*ranking|scorer.*ranking",
        ],
        check_files=["**/ranking*.py", "**/stats*.py"]
    ),

    # オフライン対応
    Requirement(
        id="MAX-005",
        name="PWA対応",
        description="インストール不要でオフライン機能を実現",
        phase=Phase.MAX,
        priority=Priority.MEDIUM,
        category="オフライン",
        check_patterns=[
            r"service.?worker|manifest\.json",
            r"pwa|offline",
        ],
        check_files=["**/manifest.json", "**/sw.js", "**/service-worker*.js"]
    ),
    Requirement(
        id="MAX-006",
        name="オフライン入力・同期",
        description="オフライン時の入力とオンライン復帰時の同期",
        phase=Phase.MAX,
        priority=Priority.MEDIUM,
        category="オフライン",
        check_patterns=[
            r"offline.*sync|sync.*offline",
            r"indexeddb|localstorage|cache",
        ],
        check_files=["**/sync*.py", "**/offline*.ts"]
    ),

    # 大会アーカイブ
    Requirement(
        id="MAX-007",
        name="年度別データ保持",
        description="年度を跨いでデータを蓄積・閲覧可能",
        phase=Phase.MAX,
        priority=Priority.LOW,
        category="アーカイブ",
        check_patterns=[
            r"year|年度|season",
            r"archive|過去",
        ],
        check_files=["**/tournament*.py", "**/archive*.py"]
    ),
]

# =============================================================================
# データエンティティ要件（requirement.mdより）
# =============================================================================
ENTITY_REQUIREMENTS = [
    Requirement(
        id="ENT-001",
        name="Tournamentエンティティ",
        description="大会名、開催日程、回数",
        phase=Phase.MINI,
        priority=Priority.HIGH,
        category="データモデル",
        check_patterns=[r"class.*Tournament", r"tournament"],
        check_files=["**/tournament*.py"]
    ),
    Requirement(
        id="ENT-002",
        name="Teamエンティティ",
        description="チーム名、地元/招待区分、会場担当フラグ",
        phase=Phase.MINI,
        priority=Priority.HIGH,
        category="データモデル",
        check_patterns=[r"class.*Team", r"team"],
        check_files=["**/team*.py"]
    ),
    Requirement(
        id="ENT-003",
        name="Playerエンティティ",
        description="背番号、選手名、所属チーム",
        phase=Phase.MINI,
        priority=Priority.MEDIUM,
        category="データモデル",
        check_patterns=[r"class.*Player", r"player"],
        check_files=["**/player*.py"]
    ),
    Requirement(
        id="ENT-004",
        name="Groupエンティティ",
        description="グループ名（A〜D）、担当会場",
        phase=Phase.MINI,
        priority=Priority.HIGH,
        category="データモデル",
        check_patterns=[r"class.*Group", r"group"],
        check_files=["**/group*.py"]
    ),
    Requirement(
        id="ENT-005",
        name="Venueエンティティ",
        description="会場名、住所、使用日",
        phase=Phase.MINI,
        priority=Priority.HIGH,
        category="データモデル",
        check_patterns=[r"class.*Venue", r"venue"],
        check_files=["**/venue*.py"]
    ),
    Requirement(
        id="ENT-006",
        name="Matchエンティティ",
        description="対戦チーム、日時、会場、スコア、ステージ",
        phase=Phase.MINI,
        priority=Priority.HIGHEST,
        category="データモデル",
        check_patterns=[r"class.*Match", r"match"],
        check_files=["**/match*.py"]
    ),
    Requirement(
        id="ENT-007",
        name="Goalエンティティ",
        description="得点時間、チーム、得点者名",
        phase=Phase.MINI,
        priority=Priority.HIGH,
        category="データモデル",
        check_patterns=[r"class.*Goal", r"goal"],
        check_files=["**/goal*.py"]
    ),
    Requirement(
        id="ENT-008",
        name="Standingエンティティ",
        description="勝点、得失点差、総得点、順位",
        phase=Phase.MINI,
        priority=Priority.HIGH,
        category="データモデル",
        check_patterns=[r"class.*Standing", r"standing"],
        check_files=["**/standing*.py"]
    ),
]

# =============================================================================
# 全要件のまとめ
# =============================================================================
ALL_REQUIREMENTS = MINI_REQUIREMENTS + MIDDLE_REQUIREMENTS + MAX_REQUIREMENTS + ENTITY_REQUIREMENTS


def get_requirements_by_phase(phase: Phase) -> list[Requirement]:
    """指定フェーズの要件を取得"""
    return [r for r in ALL_REQUIREMENTS if r.phase == phase]


def get_requirements_by_priority(priority: Priority) -> list[Requirement]:
    """指定優先度の要件を取得"""
    return [r for r in ALL_REQUIREMENTS if r.priority == priority]


def get_requirements_by_category(category: str) -> list[Requirement]:
    """指定カテゴリの要件を取得"""
    return [r for r in ALL_REQUIREMENTS if r.category == category]


def get_all_categories() -> list[str]:
    """全カテゴリを取得"""
    return list(set(r.category for r in ALL_REQUIREMENTS))
