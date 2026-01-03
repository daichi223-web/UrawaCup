"""
Match（試合）モデル
"""

from sqlalchemy import Column, Integer, String, Boolean, Date, Time, DateTime, ForeignKey, ForeignKeyConstraint, Enum
from sqlalchemy.orm import relationship
import enum

from .base import Base, TimestampMixin


class MatchStage(str, enum.Enum):
    """試合ステージ"""
    PRELIMINARY = "preliminary"   # 予選リーグ（Day1-2）
    SEMIFINAL = "semifinal"       # 準決勝（Day3）
    THIRD_PLACE = "third_place"   # 3位決定戦（Day3）
    FINAL = "final"               # 決勝（Day3）
    TRAINING = "training"         # 研修試合（Day3、2〜6位）


class MatchStatus(str, enum.Enum):
    """試合ステータス"""
    SCHEDULED = "scheduled"       # 予定
    IN_PROGRESS = "in_progress"   # 試合中
    COMPLETED = "completed"       # 完了
    CANCELLED = "cancelled"       # 中止


class MatchResult(str, enum.Enum):
    """試合結果"""
    HOME_WIN = "home_win"   # ホームチーム勝利
    AWAY_WIN = "away_win"   # アウェイチーム勝利
    DRAW = "draw"           # 引き分け


class ApprovalStatus(str, enum.Enum):
    """承認ステータス"""
    PENDING = "pending"       # 承認待ち
    APPROVED = "approved"     # 承認済み
    REJECTED = "rejected"     # 却下


class Match(Base, TimestampMixin):
    """
    試合情報テーブル
    
    予選リーグ: 各グループ12試合 × 4グループ = 48試合（Day1-2）
    決勝トーナメント: 準決勝2 + 3位決定戦1 + 決勝1 = 4試合（Day3）
    研修試合: 2〜6位の各順位で約4試合 × 5 = 約20試合（Day3）
    """
    
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(String(1), nullable=True)
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="RESTRICT"), nullable=False)
    home_team_id = Column(Integer, ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False)
    match_date = Column(Date, nullable=False, comment="試合日")
    match_time = Column(Time, nullable=False, comment="キックオフ予定時刻")
    match_order = Column(Integer, nullable=False, comment="当日の試合順（会場内通し番号）")
    stage = Column(
        Enum(MatchStage),
        nullable=False,
        default=MatchStage.PRELIMINARY,
        comment="試合ステージ"
    )
    status = Column(
        Enum(MatchStatus),
        nullable=False,
        default=MatchStatus.SCHEDULED,
        comment="試合ステータス"
    )
    
    # スコア情報
    home_score_half1 = Column(Integer, nullable=True, comment="ホームチーム前半得点")
    home_score_half2 = Column(Integer, nullable=True, comment="ホームチーム後半得点")
    home_score_total = Column(Integer, nullable=True, comment="ホームチーム合計得点")
    away_score_half1 = Column(Integer, nullable=True, comment="アウェイチーム前半得点")
    away_score_half2 = Column(Integer, nullable=True, comment="アウェイチーム後半得点")
    away_score_total = Column(Integer, nullable=True, comment="アウェイチーム合計得点")
    
    # PK戦（3位決定戦・決勝のみ）
    home_pk = Column(Integer, nullable=True, comment="ホームチームPK得点")
    away_pk = Column(Integer, nullable=True, comment="アウェイチームPK得点")
    has_penalty_shootout = Column(Boolean, nullable=False, default=False, comment="PK戦実施フラグ")
    
    # 試合結果
    result = Column(Enum(MatchResult), nullable=True, comment="試合結果")
    
    # ロック機能（同時入力防止）
    is_locked = Column(Boolean, nullable=False, default=False, comment="編集ロックフラグ")
    locked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    locked_at = Column(DateTime, nullable=True, comment="ロック日時")
    
    # 入力者情報
    entered_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    entered_at = Column(DateTime, nullable=True, comment="入力日時")

    # 承認機能
    approval_status = Column(
        Enum(ApprovalStatus),
        nullable=True,
        default=None,
        comment="承認ステータス（pending/approved/rejected）"
    )
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True, comment="承認日時")
    rejection_reason = Column(String(500), nullable=True, comment="却下理由")

    notes = Column(String(500), nullable=True, comment="備考")

    # シード情報（決勝トーナメント用）
    home_seed = Column(String(10), nullable=True, comment="ホームチームシード（例：A1位）")
    away_seed = Column(String(10), nullable=True, comment="アウェイチームシード（例：C1位）")

    # 複合外部キー制約: (tournament_id, group_id) -> groups(tournament_id, id)
    __table_args__ = (
        ForeignKeyConstraint(
            ['tournament_id', 'group_id'],
            ['groups.tournament_id', 'groups.id'],
            name='fk_matches_group',
            ondelete='SET NULL'
        ),
    )

    # リレーション
    tournament = relationship("Tournament", back_populates="matches")
    group = relationship(
        "Group",
        back_populates="matches",
        primaryjoin="and_(Match.tournament_id==Group.tournament_id, Match.group_id==Group.id)",
        foreign_keys="[Match.tournament_id, Match.group_id]",
        overlaps="tournament"
    )
    venue = relationship("Venue", back_populates="matches")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    goals = relationship("Goal", back_populates="match", cascade="all, delete-orphan")
    locked_by_user = relationship("User", foreign_keys=[locked_by])
    entered_by_user = relationship("User", foreign_keys=[entered_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<Match(id={self.id}, {self.home_team_id} vs {self.away_team_id})>"
    
    def calculate_total_scores(self):
        """合計得点を計算"""
        if self.home_score_half1 is not None and self.home_score_half2 is not None:
            self.home_score_total = self.home_score_half1 + self.home_score_half2
        if self.away_score_half1 is not None and self.away_score_half2 is not None:
            self.away_score_total = self.away_score_half1 + self.away_score_half2
    
    def determine_result(self):
        """試合結果を判定"""
        if self.home_score_total is None or self.away_score_total is None:
            self.result = None
        elif self.home_score_total > self.away_score_total:
            self.result = MatchResult.HOME_WIN
        elif self.home_score_total < self.away_score_total:
            self.result = MatchResult.AWAY_WIN
        else:
            # 同点の場合、PK戦で決着がついていればその結果を使用
            if self.has_penalty_shootout and self.home_pk is not None and self.away_pk is not None:
                if self.home_pk > self.away_pk:
                    self.result = MatchResult.HOME_WIN
                elif self.home_pk < self.away_pk:
                    self.result = MatchResult.AWAY_WIN
                else:
                    self.result = MatchResult.DRAW
            else:
                self.result = MatchResult.DRAW
