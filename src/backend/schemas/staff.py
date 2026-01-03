"""
Staff（スタッフ）スキーマ

仕様書: D:/UrawaCup/Requirement/PlayerManagement_Module_Spec.md
"""

from datetime import datetime
from typing import Optional
from pydantic import Field

from .common import CamelCaseModel


class StaffBase(CamelCaseModel):
    """スタッフ基本情報"""
    name: str = Field(..., min_length=1, max_length=100, description="氏名")
    name_kana: Optional[str] = Field(None, max_length=100, description="フリガナ")
    role: str = Field(..., max_length=50, description="役割（監督/コーチ/マネージャー/トレーナー/帯同審判）")
    phone: Optional[str] = Field(None, max_length=20, description="連絡先（携帯）")
    email: Optional[str] = Field(None, max_length=200, description="メールアドレス")
    is_primary: bool = Field(False, description="主担当（監督）")


class StaffCreate(StaffBase):
    """スタッフ作成リクエスト"""
    team_id: int = Field(..., description="チームID")


class StaffUpdate(CamelCaseModel):
    """スタッフ更新リクエスト"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    name_kana: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    is_primary: Optional[bool] = None


class StaffResponse(StaffBase):
    """スタッフレスポンス"""
    id: int
    team_id: int
    created_at: datetime
    updated_at: datetime


class StaffList(CamelCaseModel):
    """スタッフ一覧"""
    staff: list[StaffResponse]
    total: int
