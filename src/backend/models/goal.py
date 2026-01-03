"""
Goal（得点）モデル
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Goal(Base, TimestampMixin):
    """
    得点情報テーブル
    
    得点者名は自由入力も可能（登録外選手対応）。
    登録選手の場合はplayer_idで紐付け。
    """
    
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="SET NULL"), nullable=True)
    player_name = Column(String(100), nullable=False, comment="得点者名（自由入力）")
    minute = Column(Integer, nullable=False, comment="得点時間（分）")
    half = Column(Integer, nullable=False, comment="前半=1, 後半=2")
    is_own_goal = Column(Boolean, nullable=False, default=False, comment="オウンゴールフラグ")
    is_penalty = Column(Boolean, nullable=False, default=False, comment="PK得点フラグ")
    notes = Column(String(200), nullable=True, comment="備考")
    
    # リレーション
    match = relationship("Match", back_populates="goals")
    team = relationship("Team", back_populates="goals")
    player = relationship("Player", back_populates="goals")
    
    def __repr__(self):
        return f"<Goal(id={self.id}, match={self.match_id}, team={self.team_id}, minute={self.minute})>"
    
    @property
    def display_text(self) -> str:
        """報告書用の表示テキスト"""
        half_text = "前半" if self.half == 1 else "後半"
        og_text = "(OG)" if self.is_own_goal else ""
        pk_text = "(PK)" if self.is_penalty else ""
        return f"{half_text}{self.minute}分 {self.player_name}{og_text}{pk_text}"
