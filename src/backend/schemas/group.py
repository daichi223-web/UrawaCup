"""
Group（グループ）スキーマ
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel, Field

from .common import CamelCaseModel


class GroupBase(CamelCaseModel):
    """グループ基本情報"""
    id: str = Field(..., pattern="^[A-D]$", description="グループID（A, B, C, D）")
    name: str = Field(..., min_length=1, max_length=50, description="グループ名")
    venue_id: Optional[int] = Field(None, description="担当会場ID")


class GroupCreate(GroupBase):
    """グループ作成リクエスト"""
    tournament_id: int = Field(..., description="大会ID")


class GroupResponse(GroupBase):
    """グループレスポンス"""
    tournament_id: int
    created_at: datetime
    updated_at: datetime


# 循環参照を避けるため、forward referenceを使用
class GroupWithDetails(GroupResponse):
    """グループ詳細（チーム・順位含む）"""
    teams: list["TeamResponse"] = []
    standings: list["StandingWithTeam"] = []
    venue: Optional["VenueResponse"] = None


# 循環参照解決用のインポート
from .team import TeamResponse
from .standing import StandingWithTeam
from .venue import VenueResponse

GroupWithDetails.model_rebuild()
