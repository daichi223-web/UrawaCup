"""
Venue（会場）モデル
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Venue(Base, TimestampMixin):
    """
    会場情報テーブル

    4〜5会場:
    - 予選用会場（Day1-2）: 浦和南高G、市立浦和高G、浦和学院G、武南高G
    - 最終日用会場（Day3）: 駒場スタジアム（1位リーグ用）、その他3会場（研修試合用）
    """

    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, comment="会場名")
    address = Column(String(300), nullable=True, comment="住所")
    group_id = Column(String(1), nullable=True, comment="担当グループID（A, B, C, D）")
    max_matches_per_day = Column(Integer, nullable=False, default=6, comment="1日あたり最大試合数")
    for_preliminary = Column(Boolean, nullable=False, default=True, comment="予選用フラグ")
    for_final_day = Column(Boolean, nullable=False, default=False, comment="最終日用フラグ")
    is_finals_venue = Column(Boolean, nullable=False, default=False, comment="決勝会場フラグ（準決勝・3決・決勝用）")
    manager_team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, comment="会場責任チームID")
    notes = Column(String(500), nullable=True, comment="備考")

    # 複合外部キー制約: (tournament_id, group_id) -> groups(tournament_id, id)
    __table_args__ = (
        ForeignKeyConstraint(
            ['tournament_id', 'group_id'],
            ['groups.tournament_id', 'groups.id'],
            name='fk_venues_group',
            ondelete='SET NULL'
        ),
    )

    # リレーション
    tournament = relationship("Tournament", back_populates="venues")
    # 会場からグループへの参照（複合外部キー経由）
    group = relationship(
        "Group",
        primaryjoin="and_(Venue.tournament_id==Group.tournament_id, Venue.group_id==Group.id)",
        foreign_keys="[Venue.tournament_id, Venue.group_id]",
        uselist=False,
        viewonly=True
    )
    matches = relationship("Match", back_populates="venue")
    users = relationship("User", back_populates="venue")
    # 会場責任チーム
    manager_team = relationship("Team", foreign_keys=[manager_team_id])

    def __repr__(self):
        return f"<Venue(id={self.id}, name='{self.name}')>"
