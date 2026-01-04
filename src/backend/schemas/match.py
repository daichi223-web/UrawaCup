"""
Match（試合）スキーマ
"""

from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

from .common import CamelCaseModel


class MatchStage(str, Enum):
    """試合ステージ"""
    PRELIMINARY = "preliminary"
    SEMIFINAL = "semifinal"
    THIRD_PLACE = "third_place"
    FINAL = "final"
    TRAINING = "training"


class MatchStatus(str, Enum):
    """試合ステータス"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MatchResult(str, Enum):
    """試合結果"""
    HOME_WIN = "home_win"
    AWAY_WIN = "away_win"
    DRAW = "draw"


class ApprovalStatus(str, Enum):
    """承認ステータス"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MatchBase(CamelCaseModel):
    """試合基本情報"""
    venue_id: int = Field(..., description="会場ID")
    home_team_id: int = Field(..., description="ホームチームID")
    away_team_id: int = Field(..., description="アウェイチームID")
    match_date: date = Field(..., description="試合日")
    match_time: time = Field(..., description="キックオフ予定時刻")
    match_order: int = Field(..., ge=1, description="当日の試合順")
    stage: MatchStage = Field(default=MatchStage.PRELIMINARY, description="試合ステージ")


class MatchCreate(MatchBase):
    """試合作成リクエスト"""
    tournament_id: int = Field(..., description="大会ID")
    group_id: Optional[str] = Field(None, pattern="^[A-D]$", description="グループID")
    status: MatchStatus = Field(default=MatchStatus.SCHEDULED, description="試合ステータス")


class MatchUpdate(CamelCaseModel):
    """試合更新リクエスト"""
    group_id: Optional[str] = Field(None, pattern="^[A-D]$")
    venue_id: Optional[int] = None
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None
    match_date: Optional[date] = None
    match_time: Optional[time] = None
    match_order: Optional[int] = Field(None, ge=1)
    stage: Optional[MatchStage] = None
    status: Optional[MatchStatus] = None
    notes: Optional[str] = Field(None, max_length=500)
    # 運営担当（Final Day用）
    referee_main: Optional[str] = Field(None, max_length=100, description="主審")
    referee_assistant: Optional[str] = Field(None, max_length=100, description="副審")
    venue_manager: Optional[str] = Field(None, max_length=100, description="会場運営担当")


class MatchScoreInput(CamelCaseModel):
    """試合結果入力リクエスト"""
    home_score_half1: int = Field(..., ge=0, description="ホームチーム前半得点")
    home_score_half2: int = Field(..., ge=0, description="ホームチーム後半得点")
    away_score_half1: int = Field(..., ge=0, description="アウェイチーム前半得点")
    away_score_half2: int = Field(..., ge=0, description="アウェイチーム後半得点")
    home_pk: Optional[int] = Field(None, ge=0, description="ホームチームPK得点")
    away_pk: Optional[int] = Field(None, ge=0, description="アウェイチームPK得点")
    has_penalty_shootout: bool = Field(default=False, description="PK戦実施フラグ")
    goals: list["GoalInput"] = Field(default=[], description="得点情報")


class MatchResponse(CamelCaseModel):
    """試合レスポンス"""
    id: int
    tournament_id: int
    group_id: Optional[str]
    venue_id: int
    home_team_id: int
    away_team_id: int
    match_date: date
    match_time: time
    match_order: int
    stage: MatchStage
    status: MatchStatus
    home_score_half1: Optional[int]
    home_score_half2: Optional[int]
    home_score_total: Optional[int]
    away_score_half1: Optional[int]
    away_score_half2: Optional[int]
    away_score_total: Optional[int]
    home_pk: Optional[int]
    away_pk: Optional[int]
    has_penalty_shootout: bool
    result: Optional[MatchResult]
    is_locked: bool
    locked_by: Optional[int]
    locked_at: Optional[datetime]
    entered_by: Optional[int]
    entered_at: Optional[datetime]
    # 承認関連フィールド
    approval_status: Optional[ApprovalStatus] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str]
    # 運営担当（Final Day用）
    referee_main: Optional[str] = None
    referee_assistant: Optional[str] = None
    venue_manager: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MatchWithDetails(MatchResponse):
    """試合詳細（関連データ含む）"""
    home_team: "TeamResponse"
    away_team: "TeamResponse"
    venue: "VenueResponse"
    group: Optional["GroupResponse"] = None
    goals: list["GoalResponse"] = []


class MatchList(CamelCaseModel):
    """試合一覧"""
    matches: list[MatchWithDetails]
    total: int


class MatchLock(CamelCaseModel):
    """試合ロック情報"""
    match_id: int
    is_locked: bool
    locked_by: Optional[int] = None
    locked_by_name: Optional[str] = None
    locked_at: Optional[datetime] = None


class MatchApproveRequest(CamelCaseModel):
    """試合承認リクエスト"""
    user_id: int = Field(..., description="承認者のユーザーID")


class MatchRejectRequest(CamelCaseModel):
    """試合却下リクエスト"""
    user_id: int = Field(..., description="却下者のユーザーID")
    reason: str = Field(..., min_length=1, max_length=500, description="却下理由")


class MatchApprovalResponse(CamelCaseModel):
    """試合承認レスポンス"""
    match_id: int
    approval_status: ApprovalStatus
    approved_by: Optional[int] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    message: str


class PendingMatchesResponse(CamelCaseModel):
    """承認待ち試合一覧"""
    matches: list["MatchWithDetails"]
    total: int


class SwapTeamsRequest(CamelCaseModel):
    """チーム入れ替えリクエスト"""
    match1_id: int = Field(..., alias="match1Id", description="試合1のID")
    side1: str = Field(..., pattern="^(home|away)$", description="試合1のホーム/アウェイ")
    match2_id: int = Field(..., alias="match2Id", description="試合2のID")
    side2: str = Field(..., pattern="^(home|away)$", description="試合2のホーム/アウェイ")


class SwapTeamsResponse(CamelCaseModel):
    """チーム入れ替えレスポンス"""
    message: str
    match1_id: int = Field(..., alias="match1Id")
    match2_id: int = Field(..., alias="match2Id")


# 循環参照解決用のインポート
from .goal import GoalInput, GoalResponse
from .team import TeamResponse
from .venue import VenueResponse
from .group import GroupResponse

MatchScoreInput.model_rebuild()
MatchWithDetails.model_rebuild()
PendingMatchesResponse.model_rebuild()
