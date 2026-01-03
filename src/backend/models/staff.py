"""
Staff（スタッフ）モデル

監督、コーチ、マネージャー、帯同審判員等を管理。
仕様書: D:/UrawaCup/Requirement/PlayerManagement_Module_Spec.md
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Staff(Base, TimestampMixin):
    """
    スタッフ情報テーブル

    チームに所属する監督、コーチ等のスタッフ情報。
    参加申込書からのインポートで使用。
    """

    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)

    # 基本情報
    name = Column(String(100), nullable=False, comment="氏名")
    name_kana = Column(String(100), nullable=True, comment="フリガナ")
    role = Column(String(50), nullable=False, comment="役割（監督/コーチ/マネージャー/トレーナー/帯同審判）")

    # 連絡先
    phone = Column(String(20), nullable=True, comment="連絡先（携帯）")
    email = Column(String(200), nullable=True, comment="メールアドレス")

    # フラグ
    is_primary = Column(Boolean, nullable=False, default=False, comment="主担当（監督）")

    # リレーション
    team = relationship("Team", back_populates="staff_members")

    # インデックス
    __table_args__ = (
        Index('idx_staff_team', 'team_id'),
    )

    def __repr__(self):
        return f"<Staff(id={self.id}, role='{self.role}', name='{self.name}')>"

    @property
    def display_text(self) -> str:
        """表示用テキスト"""
        return f"{self.role}: {self.name}"
