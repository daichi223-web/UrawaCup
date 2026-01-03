"""
ReportRecipient（報告書送信先）モデル
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class ReportRecipient(Base):
    """
    報告書送信先テーブル
    
    固定送信先:
    - 埼玉新聞
    - テレビ埼玉
    - イシクラ
    - 埼玉県サッカー協会
    """
    
    __tablename__ = "report_recipients"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, comment="送信先名")
    email = Column(String(255), nullable=True, comment="メールアドレス")
    fax = Column(String(50), nullable=True, comment="FAX番号")
    notes = Column(String(200), nullable=True, comment="備考")
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="作成日時"
    )
    
    # リレーション
    tournament = relationship("Tournament", back_populates="report_recipients")
    
    def __repr__(self):
        return f"<ReportRecipient(id={self.id}, name='{self.name}')>"
