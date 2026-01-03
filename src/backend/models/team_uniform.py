"""
TeamUniform（チームユニフォーム）モデル

GK/FPの正副ユニフォーム情報を管理。
仕様書: D:/UrawaCup/Requirement/PlayerManagement_Module_Spec.md
"""

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base


class TeamUniform(Base):
    """
    ユニフォーム情報テーブル

    各チームのGK/FPのユニフォーム色情報。
    参加申込書からのインポートで使用。
    """

    __tablename__ = "team_uniforms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)

    # 種別
    player_type = Column(String(10), nullable=False, comment="GK / FP")
    uniform_type = Column(String(10), nullable=False, comment="primary / secondary")

    # 色情報
    shirt_color = Column(String(50), nullable=True, comment="シャツの色")
    pants_color = Column(String(50), nullable=True, comment="パンツの色")
    socks_color = Column(String(50), nullable=True, comment="ストッキングの色")

    # リレーション
    team = relationship("Team", back_populates="uniforms")

    # ユニーク制約: チーム×選手種別×ユニフォーム種別
    __table_args__ = (
        UniqueConstraint('team_id', 'player_type', 'uniform_type', name='uq_team_uniform'),
    )

    def __repr__(self):
        return f"<TeamUniform(team={self.team_id}, {self.player_type} {self.uniform_type})>"

    @property
    def display_text(self) -> str:
        """表示用テキスト"""
        type_display = "正" if self.uniform_type == "primary" else "副"
        colors = f"{self.shirt_color or '-'}/{self.pants_color or '-'}/{self.socks_color or '-'}"
        return f"{self.player_type} ({type_display}): {colors}"
