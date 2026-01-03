"""
SQLAlchemy ベースモデル
"""

from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TimestampMixin:
    """作成日時・更新日時を持つモデル用のMixin"""
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="作成日時"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新日時"
    )
