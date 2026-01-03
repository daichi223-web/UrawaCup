"""
Tournament（大会）モデル
"""

from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Tournament(Base, TimestampMixin):
    """
    大会情報テーブル
    
    浦和カップは年度ごとに1レコード。
    大会名、開催期間、試合時間などの基本設定を保持。
    """
    
    __tablename__ = "tournaments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="大会名")
    short_name = Column(String(100), nullable=True, comment="大会略称（ヘッダー表示用）")
    edition = Column(Integer, nullable=False, default=1, comment="開催回数（第○回）")
    year = Column(Integer, nullable=False, comment="開催年度")
    start_date = Column(Date, nullable=False, comment="開始日")
    end_date = Column(Date, nullable=False, comment="終了日")
    match_duration = Column(Integer, nullable=False, default=50, comment="試合時間（分）")
    half_duration = Column(Integer, nullable=False, default=25, comment="ハーフタイム（分）")
    interval_minutes = Column(Integer, nullable=False, default=15, comment="試合間インターバル（分）")

    # 報告書発信元情報
    sender_organization = Column(String(100), nullable=True, comment="発信元所属（例：県立浦和高校）")
    sender_name = Column(String(100), nullable=True, comment="発信元氏名（例：森川大地）")
    sender_contact = Column(String(100), nullable=True, comment="発信元連絡先（例：090-XXXX-XXXX）")
    
    # リレーション
    teams = relationship("Team", back_populates="tournament", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="tournament", cascade="all, delete-orphan")
    venues = relationship("Venue", back_populates="tournament", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="tournament", cascade="all, delete-orphan")
    standings = relationship("Standing", back_populates="tournament", cascade="all, delete-orphan")
    exclusion_pairs = relationship("ExclusionPair", back_populates="tournament", cascade="all, delete-orphan")
    report_recipients = relationship("ReportRecipient", back_populates="tournament", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tournament(id={self.id}, name='{self.name}', year={self.year})>"
