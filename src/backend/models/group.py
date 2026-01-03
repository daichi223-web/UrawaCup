"""
Group（グループ）モデル
"""

from sqlalchemy import Column, Integer, String, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Group(Base, TimestampMixin):
    """
    グループ情報テーブル

    4グループ固定: A, B, C, D
    各グループに6チームが所属。

    複合主キー: (tournament_id, id)
    これにより、異なる大会で同じグループID（A, B, C, D）を使用可能。
    """

    __tablename__ = "groups"

    # 複合主キー: tournament_idとidの組み合わせでユニーク
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    # グループIDは A, B, C, D の1文字
    id = Column(String(1), nullable=False)
    name = Column(String(50), nullable=False, comment="グループ名（表示用）")
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="SET NULL"), nullable=True)

    # 複合主キー制約
    __table_args__ = (
        PrimaryKeyConstraint('tournament_id', 'id', name='pk_groups'),
    )

    # リレーション
    tournament = relationship("Tournament", back_populates="groups")
    # グループから会場への参照（venue_id経由）
    venue = relationship(
        "Venue",
        primaryjoin="Group.venue_id==Venue.id",
        foreign_keys=[venue_id],
        uselist=False
    )
    teams = relationship(
        "Team",
        back_populates="group",
        primaryjoin="and_(Group.tournament_id==Team.tournament_id, Group.id==Team.group_id)",
        foreign_keys="[Team.tournament_id, Team.group_id]",
        overlaps="tournament"
    )
    matches = relationship(
        "Match",
        back_populates="group",
        primaryjoin="and_(Group.tournament_id==Match.tournament_id, Group.id==Match.group_id)",
        foreign_keys="[Match.tournament_id, Match.group_id]",
        overlaps="tournament"
    )
    standings = relationship(
        "Standing",
        back_populates="group",
        primaryjoin="and_(Group.tournament_id==Standing.tournament_id, Group.id==Standing.group_id)",
        foreign_keys="[Standing.tournament_id, Standing.group_id]",
        overlaps="tournament"
    )
    exclusion_pairs = relationship(
        "ExclusionPair",
        back_populates="group",
        primaryjoin="and_(Group.tournament_id==ExclusionPair.tournament_id, Group.id==ExclusionPair.group_id)",
        foreign_keys="[ExclusionPair.tournament_id, ExclusionPair.group_id]",
        overlaps="tournament"
    )

    def __repr__(self):
        return f"<Group(tournament_id={self.tournament_id}, id='{self.id}', name='{self.name}')>"
