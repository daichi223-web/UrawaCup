"""
Standing（順位表）スキーマ
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from .common import CamelCaseModel


class StandingBase(CamelCaseModel):
    """順位基本情報"""
    rank: int = Field(..., ge=1, le=6, description="順位")
    played: int = Field(default=0, ge=0, description="試合数")
    won: int = Field(default=0, ge=0, description="勝利数")
    drawn: int = Field(default=0, ge=0, description="引分数")
    lost: int = Field(default=0, ge=0, description="敗北数")
    goals_for: int = Field(default=0, ge=0, description="総得点")
    goals_against: int = Field(default=0, ge=0, description="総失点")
    goal_difference: int = Field(default=0, description="得失点差")
    points: int = Field(default=0, ge=0, description="勝点")
    rank_reason: Optional[str] = Field(None, max_length=100, description="順位決定理由")


class StandingResponse(StandingBase):
    """順位レスポンス"""
    id: int
    tournament_id: int
    group_id: str
    team_id: int
    updated_at: datetime


class StandingWithTeam(StandingResponse):
    """順位表（チーム情報付き）"""
    team: "TeamResponse"


class GroupStanding(CamelCaseModel):
    """グループ順位表"""
    group: "GroupResponse"
    standings: list[StandingWithTeam]


class HeadToHead(CamelCaseModel):
    """直接対決成績（同勝点時の順位決定用）"""
    team1_id: int
    team2_id: int
    team1_wins: int = 0
    team2_wins: int = 0
    draws: int = 0
    team1_goals: int = 0
    team2_goals: int = 0


# 循環参照解決用のインポート
from .team import TeamResponse
from .group import GroupResponse

StandingWithTeam.model_rebuild()
GroupStanding.model_rebuild()
