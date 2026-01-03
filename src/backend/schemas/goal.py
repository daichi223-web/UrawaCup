"""
Goal（得点）スキーマ
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

from .common import CamelCaseModel


class GoalBase(CamelCaseModel):
    """得点基本情報"""
    team_id: int = Field(..., description="得点チームID")
    player_id: Optional[int] = Field(None, description="得点者ID（登録選手の場合）")
    player_name: str = Field(..., min_length=1, max_length=100, description="得点者名")
    minute: int = Field(..., ge=0, le=90, description="得点時間（分）")
    half: Literal[1, 2] = Field(..., description="前半=1, 後半=2")
    is_own_goal: bool = Field(default=False, description="オウンゴールフラグ")
    is_penalty: bool = Field(default=False, description="PK得点フラグ")
    notes: Optional[str] = Field(None, max_length=200, description="備考")


class GoalCreate(GoalBase):
    """得点作成リクエスト"""
    match_id: int = Field(..., description="試合ID")


class GoalUpdate(CamelCaseModel):
    """得点更新リクエスト"""
    team_id: Optional[int] = None
    player_id: Optional[int] = None
    player_name: Optional[str] = Field(None, min_length=1, max_length=100)
    minute: Optional[int] = Field(None, ge=0, le=90)
    half: Optional[Literal[1, 2]] = None
    is_own_goal: Optional[bool] = None
    is_penalty: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=200)


class GoalInput(CamelCaseModel):
    """得点入力フォーム（試合結果入力時に使用）"""
    team_id: int
    player_id: Optional[int] = None
    player_name: str = Field(..., min_length=1, max_length=100)
    minute: int = Field(..., ge=0, le=90)
    half: Literal[1, 2]
    is_own_goal: bool = False
    is_penalty: bool = False
    notes: Optional[str] = None


class GoalResponse(GoalBase):
    """得点レスポンス"""
    id: int
    match_id: int
    created_at: datetime
    updated_at: datetime


class GoalDetail(GoalResponse):
    """得点詳細（報告書用）"""
    team_name: str
    is_home: bool

    @property
    def display_text(self) -> str:
        """報告書用の表示テキスト"""
        half_text = "前半" if self.half == 1 else "後半"
        og_text = "(OG)" if self.is_own_goal else ""
        pk_text = "(PK)" if self.is_penalty else ""
        return f"{half_text}{self.minute}分 {self.team_name} {self.player_name}{og_text}{pk_text}"
