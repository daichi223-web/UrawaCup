"""
ExclusionPair（対戦除外設定）モデル
"""

from sqlalchemy import Column, Integer, String, ForeignKey, ForeignKeyConstraint, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class ExclusionPair(Base):
    """
    対戦除外設定テーブル（変則リーグ用）

    6チーム変則リーグでは各チーム4試合（2チームとは対戦しない）。
    対戦しないペアを手動で設定する。

    除外の判断基準（運用ルール）:
    - 地元校同士の対戦を避ける
    - 近い地域のチーム同士を避ける
    - 他大会で同じリーグに所属するチーム同士を避ける
    """

    __tablename__ = "exclusion_pairs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(String(1), nullable=False)
    team1_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    team2_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String(200), nullable=True, comment="除外理由")
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="作成日時"
    )

    # 複合外部キー制約: (tournament_id, group_id) -> groups(tournament_id, id)
    __table_args__ = (
        ForeignKeyConstraint(
            ['tournament_id', 'group_id'],
            ['groups.tournament_id', 'groups.id'],
            name='fk_exclusion_pairs_group',
            ondelete='CASCADE'
        ),
    )

    # リレーション
    tournament = relationship("Tournament", back_populates="exclusion_pairs")
    group = relationship(
        "Group",
        back_populates="exclusion_pairs",
        primaryjoin="and_(ExclusionPair.tournament_id==Group.tournament_id, ExclusionPair.group_id==Group.id)",
        foreign_keys="[ExclusionPair.tournament_id, ExclusionPair.group_id]",
        overlaps="tournament"
    )
    team1 = relationship("Team", foreign_keys=[team1_id])
    team2 = relationship("Team", foreign_keys=[team2_id])

    def __repr__(self):
        return f"<ExclusionPair(group={self.group_id}, team1={self.team1_id}, team2={self.team2_id})>"
