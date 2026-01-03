"""
Team（チーム）モデル
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, ForeignKeyConstraint
from sqlalchemy.orm import relationship
import enum

from .base import Base, TimestampMixin


class TeamType(str, enum.Enum):
    """チーム区分"""
    LOCAL = "local"      # 地元チーム
    INVITED = "invited"  # 招待チーム


class Team(Base, TimestampMixin):
    """
    チーム情報テーブル

    24チーム固定:
    - 地元チーム9チーム（会場担当校4校を含む）
    - 招待チーム15チーム

    会場担当校は各グループの1番に固定配置:
    - A1: 浦和南
    - B1: 市立浦和
    - C1: 浦和学院
    - D1: 武南
    """

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, comment="チーム名")
    short_name = Column(String(50), nullable=True, comment="チーム略称（報告書用）")
    team_type = Column(
        Enum(TeamType),
        nullable=False,
        default=TeamType.INVITED,
        comment="地元/招待の区分"
    )
    is_venue_host = Column(Boolean, nullable=False, default=False, comment="会場担当校フラグ")
    group_id = Column(String(1), nullable=True)
    group_order = Column(Integer, nullable=True, comment="グループ内番号（1-6）")
    prefecture = Column(String(20), nullable=True, comment="都道府県")
    notes = Column(String(500), nullable=True, comment="備考")

    # 複合外部キー制約: (tournament_id, group_id) -> groups(tournament_id, id)
    __table_args__ = (
        ForeignKeyConstraint(
            ['tournament_id', 'group_id'],
            ['groups.tournament_id', 'groups.id'],
            name='fk_teams_group',
            ondelete='SET NULL'
        ),
    )

    # リレーション
    tournament = relationship("Tournament", back_populates="teams")
    group = relationship(
        "Group",
        primaryjoin="and_(Team.tournament_id==Group.tournament_id, Team.group_id==Group.id)",
        foreign_keys="[Team.tournament_id, Team.group_id]",
        back_populates="teams",
        overlaps="tournament"
    )
    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")
    staff_members = relationship("Staff", back_populates="team", cascade="all, delete-orphan")
    uniforms = relationship("TeamUniform", back_populates="team", cascade="all, delete-orphan")
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")
    goals = relationship("Goal", back_populates="team")
    standings = relationship("Standing", back_populates="team")

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}', group={self.group_id}{self.group_order})>"
