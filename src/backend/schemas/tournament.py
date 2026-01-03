"""
Tournament（大会）スキーマ
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field

from .common import CamelCaseModel


class TournamentBase(CamelCaseModel):
    """大会基本情報"""
    name: str = Field(..., min_length=1, max_length=200, description="大会名")
    short_name: Optional[str] = Field(None, max_length=100, description="大会略称")
    edition: int = Field(default=1, ge=1, description="開催回数（第○回）")
    year: int = Field(..., ge=2000, le=2100, description="開催年度")
    start_date: date = Field(..., description="開始日")
    end_date: date = Field(..., description="終了日")
    match_duration: int = Field(default=50, ge=10, le=120, description="試合時間（分）")
    half_duration: int = Field(default=25, ge=5, le=60, description="ハーフタイム（分）")
    interval_minutes: int = Field(default=15, ge=5, le=60, description="試合間インターバル（分）")
    # 報告書発信元情報
    sender_organization: Optional[str] = Field(None, max_length=100, description="発信元所属")
    sender_name: Optional[str] = Field(None, max_length=100, description="発信元氏名")
    sender_contact: Optional[str] = Field(None, max_length=100, description="発信元連絡先")


class TournamentCreate(TournamentBase):
    """大会作成リクエスト"""
    pass


class TournamentUpdate(CamelCaseModel):
    """大会更新リクエスト"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    short_name: Optional[str] = Field(None, max_length=100)
    edition: Optional[int] = Field(None, ge=1)
    year: Optional[int] = Field(None, ge=2000, le=2100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    match_duration: Optional[int] = Field(None, ge=10, le=120)
    half_duration: Optional[int] = Field(None, ge=5, le=60)
    interval_minutes: Optional[int] = Field(None, ge=5, le=60)
    # 報告書発信元情報
    sender_organization: Optional[str] = Field(None, max_length=100)
    sender_name: Optional[str] = Field(None, max_length=100)
    sender_contact: Optional[str] = Field(None, max_length=100)


class TournamentResponse(TournamentBase):
    """大会レスポンス"""
    id: int
    created_at: datetime
    updated_at: datetime


class TournamentList(CamelCaseModel):
    """大会一覧"""
    tournaments: list[TournamentResponse]
    total: int
