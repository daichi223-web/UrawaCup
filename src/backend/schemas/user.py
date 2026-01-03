"""
User（ユーザー）スキーマ
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from enum import Enum

from .common import CamelCaseModel


class UserRole(str, Enum):
    """ユーザー権限"""
    ADMIN = "admin"
    VENUE_STAFF = "venue_staff"
    VIEWER = "viewer"


class UserBase(CamelCaseModel):
    """ユーザー基本情報"""
    username: str = Field(..., min_length=3, max_length=50, description="ユーザー名")
    display_name: str = Field(..., min_length=1, max_length=100, description="表示名")
    email: Optional[EmailStr] = Field(None, description="メールアドレス")
    role: UserRole = Field(default=UserRole.VIEWER, description="権限")
    venue_id: Optional[int] = Field(None, description="担当会場ID")


class UserCreate(UserBase):
    """ユーザー作成リクエスト"""
    password: str = Field(..., min_length=8, max_length=100, description="パスワード")


class UserUpdate(CamelCaseModel):
    """ユーザー更新リクエスト"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    venue_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """ユーザーレスポンス"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LoginRequest(CamelCaseModel):
    """ログインリクエスト"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(CamelCaseModel):
    """ログインレスポンス（camelCase対応）"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class AuthUser(CamelCaseModel):
    """認証済みユーザー情報"""
    id: int
    username: str
    display_name: str
    role: UserRole
    venue_id: Optional[int] = None
