"""
Venue（会場）スキーマ
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from .common import CamelCaseModel


class VenueBase(CamelCaseModel):
    """会場基本情報"""
    name: str = Field(..., min_length=1, max_length=100, description="会場名")
    address: Optional[str] = Field(None, max_length=300, description="住所")
    group_id: Optional[str] = Field(None, pattern="^[A-D]$", description="担当グループID")
    max_matches_per_day: int = Field(default=6, ge=1, le=20, description="1日あたり最大試合数")
    for_preliminary: bool = Field(default=True, description="予選用フラグ")
    for_final_day: bool = Field(default=False, description="最終日用フラグ")
    is_finals_venue: bool = Field(default=False, description="決勝会場フラグ（準決勝・3決・決勝用）")
    manager_team_id: Optional[int] = Field(None, description="会場責任チームID")
    notes: Optional[str] = Field(None, max_length=500, description="備考")


class VenueCreate(VenueBase):
    """会場作成リクエスト"""
    tournament_id: int = Field(..., description="大会ID")


class VenueUpdate(CamelCaseModel):
    """会場更新リクエスト"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=300)
    group_id: Optional[str] = Field(None, pattern="^[A-D]$")
    max_matches_per_day: Optional[int] = Field(None, ge=1, le=20)
    for_preliminary: Optional[bool] = None
    for_final_day: Optional[bool] = None
    is_finals_venue: Optional[bool] = None
    manager_team_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=500)


class VenueResponse(VenueBase):
    """会場レスポンス"""
    id: int
    tournament_id: int
    created_at: datetime
    updated_at: datetime


class VenueList(CamelCaseModel):
    """会場一覧"""
    venues: list[VenueResponse]
    total: int


class VenueSchedule(CamelCaseModel):
    """会場の日程情報"""
    venue_id: int
    date: str = Field(..., description="日付（YYYY-MM-DD）")
    start_time: str = Field(..., description="開始時刻（HH:mm）")
    end_time: str = Field(..., description="終了時刻（HH:mm）")
    match_count: int
