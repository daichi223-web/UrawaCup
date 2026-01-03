"""
User（ユーザー）モデル
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from .base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    """ユーザー権限"""
    ADMIN = "admin"              # 管理者（全機能）
    VENUE_STAFF = "venue_staff"  # 会場担当者（担当会場の入力のみ）
    VIEWER = "viewer"            # 閲覧者（閲覧のみ）


class User(Base, TimestampMixin):
    """
    ユーザー情報テーブル
    
    権限レベル:
    - admin: 全機能にアクセス可能
    - venue_staff: 担当会場の試合結果入力のみ
    - viewer: 閲覧のみ（認証不要で閲覧可能にする場合は不要）
    """
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True, comment="ユーザー名（ログイン用）")
    password_hash = Column(String(255), nullable=False, comment="パスワードハッシュ")
    display_name = Column(String(100), nullable=False, comment="表示名")
    email = Column(String(255), nullable=True, comment="メールアドレス")
    role = Column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.VIEWER,
        comment="権限"
    )
    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, comment="有効フラグ")
    
    # リレーション
    venue = relationship("Venue", back_populates="users")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role={self.role})>"
    
    def can_edit_venue(self, venue_id: int) -> bool:
        """指定会場の編集権限があるか確認"""
        if self.role == UserRole.ADMIN:
            return True
        if self.role == UserRole.VENUE_STAFF and self.venue_id == venue_id:
            return True
        return False
    
    def can_edit_match(self, match) -> bool:
        """指定試合の編集権限があるか確認"""
        if self.role == UserRole.ADMIN:
            return True
        if self.role == UserRole.VENUE_STAFF and self.venue_id == match.venue_id:
            return True
        return False
