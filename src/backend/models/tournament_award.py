"""
TournamentAward（大会表彰）モデル

最終順位と優秀選手を管理
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base


class AwardType(str, enum.Enum):
    """表彰種別"""
    MVP = "mvp"                    # 最優秀選手
    OUTSTANDING = "outstanding"    # 優秀選手


class TournamentFinalRanking(Base):
    """
    大会最終順位テーブル

    決勝トーナメント終了後の1-4位を記録
    """

    __tablename__ = "tournament_final_rankings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    rank = Column(Integer, nullable=False, comment="順位（1-4）")
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # リレーション
    tournament = relationship("Tournament")
    team = relationship("Team")

    def __repr__(self):
        return f"<TournamentFinalRanking(tournament={self.tournament_id}, rank={self.rank}, team={self.team_id})>"


class OutstandingPlayer(Base):
    """
    優秀選手テーブル

    大会終了後の表彰選手を記録
    仕様書: D:/UrawaCup/Requirement/PlayerManagement_Module_Spec.md
    """

    __tablename__ = "outstanding_players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    award_type = Column(
        Enum(AwardType),
        nullable=False,
        default=AwardType.OUTSTANDING,
        comment="表彰種別"
    )
    player_name = Column(String(100), nullable=False, comment="選手名")
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="SET NULL"), nullable=True, comment="選手ID（登録済みの場合）")
    display_order = Column(Integer, nullable=False, default=0, comment="表示順")
    notes = Column(String(500), nullable=True, comment="選出理由等")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # リレーション
    tournament = relationship("Tournament")
    team = relationship("Team")
    player = relationship("Player")

    def __repr__(self):
        return f"<OutstandingPlayer(tournament={self.tournament_id}, award={self.award_type}, player={self.player_name})>"

    @property
    def award_display(self) -> str:
        """表彰名を表示用に変換"""
        if self.award_type == AwardType.MVP:
            return "最優秀選手"
        return "優秀選手"
