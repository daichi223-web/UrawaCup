"""
Standing（順位表）モデル
"""

from sqlalchemy import Column, Integer, String, ForeignKey, ForeignKeyConstraint, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class Standing(Base):
    """
    順位情報テーブル

    順位決定ルール（優先順位）:
    1. 勝点（勝利=3点、引分=1点、敗北=0点）
    2. 得失点差
    3. 総得点
    4. 当該チーム間の対戦成績
    5. 抽選
    """

    __tablename__ = "standings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(String(1), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    rank = Column(Integer, nullable=False, default=0, comment="順位")
    played = Column(Integer, nullable=False, default=0, comment="試合数")
    won = Column(Integer, nullable=False, default=0, comment="勝利数")
    drawn = Column(Integer, nullable=False, default=0, comment="引分数")
    lost = Column(Integer, nullable=False, default=0, comment="敗北数")
    goals_for = Column(Integer, nullable=False, default=0, comment="総得点")
    goals_against = Column(Integer, nullable=False, default=0, comment="総失点")
    goal_difference = Column(Integer, nullable=False, default=0, comment="得失点差")
    points = Column(Integer, nullable=False, default=0, comment="勝点")
    rank_reason = Column(String(100), nullable=True, comment="順位決定理由（同勝点時に記録）")
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="最終更新日時"
    )

    # 複合外部キー制約: (tournament_id, group_id) -> groups(tournament_id, id)
    __table_args__ = (
        ForeignKeyConstraint(
            ['tournament_id', 'group_id'],
            ['groups.tournament_id', 'groups.id'],
            name='fk_standings_group',
            ondelete='CASCADE'
        ),
    )

    # リレーション
    tournament = relationship("Tournament", back_populates="standings")
    group = relationship(
        "Group",
        back_populates="standings",
        primaryjoin="and_(Standing.tournament_id==Group.tournament_id, Standing.group_id==Group.id)",
        foreign_keys="[Standing.tournament_id, Standing.group_id]",
        overlaps="tournament"
    )
    team = relationship("Team", back_populates="standings")
    
    def __repr__(self):
        return f"<Standing(group={self.group_id}, team={self.team_id}, rank={self.rank}, points={self.points})>"
    
    def reset(self):
        """順位情報をリセット"""
        self.rank = 0
        self.played = 0
        self.won = 0
        self.drawn = 0
        self.lost = 0
        self.goals_for = 0
        self.goals_against = 0
        self.goal_difference = 0
        self.points = 0
        self.rank_reason = None
    
    def calculate_derived_values(self):
        """得失点差と勝点を計算"""
        self.goal_difference = self.goals_for - self.goals_against
        self.points = (self.won * 3) + (self.drawn * 1)
