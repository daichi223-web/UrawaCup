"""
ExclusionPair（対戦除外設定）スキーマ
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from .common import CamelCaseModel


class ExclusionPairBase(CamelCaseModel):
    """対戦除外設定基本情報"""
    group_id: str = Field(..., pattern="^[A-D]$", description="グループID")
    team1_id: int = Field(..., description="除外チーム1のID")
    team2_id: int = Field(..., description="除外チーム2のID")
    reason: Optional[str] = Field(None, max_length=200, description="除外理由")


class ExclusionPairCreate(ExclusionPairBase):
    """対戦除外設定作成リクエスト"""
    tournament_id: int = Field(..., description="大会ID")


class ExclusionPairResponse(ExclusionPairBase):
    """対戦除外設定レスポンス"""
    id: int
    tournament_id: int
    created_at: datetime


class GroupExclusions(CamelCaseModel):
    """グループの除外設定一覧"""
    group_id: str
    exclusions: list[ExclusionPairResponse]
    team_exclusion_count: dict[int, int] = Field(
        default={},
        description="各チームの除外数マップ"
    )
    is_complete: bool = Field(
        default=False,
        description="設定完了フラグ（全チームが2チームずつ除外設定済み）"
    )
