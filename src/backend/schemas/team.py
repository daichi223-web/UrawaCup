"""
Team（チーム）スキーマ
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel, Field
from enum import Enum

from .common import CamelCaseModel


class TeamType(str, Enum):
    """チーム区分"""
    LOCAL = "local"
    INVITED = "invited"


class TeamBase(CamelCaseModel):
    """チーム基本情報"""
    name: str = Field(..., min_length=1, max_length=100, description="チーム名")
    short_name: Optional[str] = Field(None, max_length=50, description="チーム略称")
    team_type: TeamType = Field(default=TeamType.INVITED, description="地元/招待の区分")
    is_venue_host: bool = Field(default=False, description="会場担当校フラグ")
    group_id: Optional[str] = Field(None, pattern="^[A-D]$", description="所属グループ")
    group_order: Optional[int] = Field(None, ge=1, le=6, description="グループ内番号")
    prefecture: Optional[str] = Field(None, max_length=20, description="都道府県")
    notes: Optional[str] = Field(None, max_length=500, description="備考")


class TeamCreate(TeamBase):
    """チーム作成リクエスト"""
    tournament_id: int = Field(..., description="大会ID")


class TeamUpdate(CamelCaseModel):
    """チーム更新リクエスト"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    short_name: Optional[str] = Field(None, max_length=50)
    team_type: Optional[TeamType] = None
    is_venue_host: Optional[bool] = None
    group_id: Optional[str] = Field(None, pattern="^[A-D]$")
    group_order: Optional[int] = Field(None, ge=1, le=6)
    prefecture: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=500)


class TeamResponse(TeamBase):
    """チームレスポンス"""
    id: int
    tournament_id: int
    created_at: datetime
    updated_at: datetime


class TeamList(CamelCaseModel):
    """チーム一覧"""
    teams: list[TeamResponse]
    total: int


# 循環参照を避けるため、forward referenceを使用
class TeamWithDetails(TeamResponse):
    """チーム詳細（関連データ含む）"""
    players: list["PlayerResponse"] = []
    group: Optional["GroupResponse"] = None


# 循環参照解決用のインポート
from .player import PlayerResponse
from .group import GroupResponse

TeamWithDetails.model_rebuild()
