"""
報告書用データ型定義

TournaMate_Report_Formats.md のデータ構造に基づく
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List


@dataclass
class GoalData:
    """得点情報"""
    minute: int                  # 得点時間（分）
    half: int                    # 1=前半, 2=後半
    team_name: str               # チーム名
    scorer_name: str             # 得点者名
    is_own_goal: bool = False    # オウンゴール
    is_penalty: bool = False     # PK

    @property
    def display_minute(self) -> int:
        """表示用の時間（後半は+25分）"""
        if self.half == 2:
            return self.minute + 25  # 前半25分想定
        return self.minute


@dataclass
class MatchResultData:
    """試合結果データ"""
    match_number: int            # 試合番号
    kickoff_time: str            # キックオフ時刻 "HH:MM"
    home_team: str               # ホームチーム名
    away_team: str               # アウェイチーム名
    home_score_half1: int        # ホーム前半得点
    home_score_half2: int        # ホーム後半得点
    away_score_half1: int        # アウェイ前半得点
    away_score_half2: int        # アウェイ後半得点
    has_penalty_shootout: bool = False
    home_pk: Optional[int] = None
    away_pk: Optional[int] = None
    goals: List[GoalData] = field(default_factory=list)

    @property
    def home_score_total(self) -> int:
        return self.home_score_half1 + self.home_score_half2

    @property
    def away_score_total(self) -> int:
        return self.away_score_half1 + self.away_score_half2

    @property
    def score_display(self) -> str:
        """スコア表示文字列"""
        pk_str = ""
        if self.has_penalty_shootout:
            pk_str = f" (PK {self.home_pk}-{self.away_pk})"
        return f"{self.home_score_total} - {self.away_score_total}{pk_str}"


@dataclass
class SenderInfo:
    """発信元情報"""
    organization: str            # 所属（"県立浦和高校"）
    name: str                    # 氏名（"森川大地"）
    contact: str                 # 連絡先（"090-XXXX-XXXX"）


@dataclass
class VenueInfo:
    """会場情報"""
    id: int
    name: str                    # 会場名（"浦和南高G"）
    group_id: Optional[str] = None


@dataclass
class TournamentInfo:
    """大会情報"""
    id: int
    name: str                    # "第44回 浦和カップ高校サッカーフェスティバル"
    edition: int                 # 44
    start_date: date


@dataclass
class DailyReportData:
    """
    日次試合結果報告書データ

    TournaMate_Report_Formats.md Section 2 に基づく
    """
    tournament: TournamentInfo
    report_date: date            # 報告対象日
    day_number: int              # 第N日
    venue: VenueInfo
    sender: SenderInfo
    recipients: List[str]        # 送信先名リスト
    matches: List[MatchResultData]
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class FinalRanking:
    """最終順位"""
    rank: int                    # 1, 2, 3, 4
    team_name: str


@dataclass
class OutstandingPlayer:
    """優秀選手"""
    award: str                   # "最優秀選手" | "優秀選手"
    player_name: str
    team_name: str


@dataclass
class KnockoutMatch:
    """決勝トーナメント試合"""
    round_name: str              # "準決勝1" | "準決勝2" | "3位決定戦" | "決勝"
    home_seed: str               # "A1位"
    home_team: str               # "浦和南"
    away_seed: str               # "C1位"
    away_team: str               # "浦和学院"
    home_score_half1: int
    home_score_half2: int
    away_score_half1: int
    away_score_half2: int
    has_penalty_shootout: bool = False
    home_pk: Optional[int] = None
    away_pk: Optional[int] = None


@dataclass
class FinalReportData:
    """
    最終結果報告書データ

    TournaMate_Report_Formats.md Section 4 に基づく
    """
    tournament: TournamentInfo
    knockout_results: List[KnockoutMatch]
    final_rankings: List[FinalRanking]
    outstanding_players: List[OutstandingPlayer]
    training_matches: List[MatchResultData] = field(default_factory=list)


@dataclass
class FinalDayMatch:
    """最終日試合"""
    match_number: int
    kickoff_time: str            # "9:30"
    home_team: str               # チーム名 or "4位③"
    away_team: str
    match_type: Optional[str] = None  # "準決勝" | "3位決" | "決勝" | "研修"
    referee_main: str = "当該"
    referee_assistant: str = "当該"


@dataclass
class FinalDayVenueSchedule:
    """最終日会場スケジュール"""
    venue_name: str
    venue_manager: str           # 会場責任チーム
    matches: List[FinalDayMatch]


@dataclass
class FinalDayScheduleData:
    """
    最終日組み合わせ表データ

    TournaMate_Report_Formats.md Section 3 に基づく
    """
    date: date
    ranking_league_venues: List[FinalDayVenueSchedule]  # 順位リーグ
    knockout_venue: FinalDayVenueSchedule               # 3決・決勝戦
