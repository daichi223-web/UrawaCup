"""
Report（報告書）スキーマ
"""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr

from .common import CamelCaseModel


class ReportRecipientBase(CamelCaseModel):
    """報告書送信先基本情報"""
    name: str = Field(..., min_length=1, max_length=100, description="送信先名")
    email: Optional[EmailStr] = Field(None, description="メールアドレス")
    fax: Optional[str] = Field(None, max_length=50, description="FAX番号")
    notes: Optional[str] = Field(None, max_length=200, description="備考")


class ReportRecipientCreate(ReportRecipientBase):
    """報告書送信先作成リクエスト"""
    tournament_id: int = Field(..., description="大会ID")


class SenderSettingsUpdate(CamelCaseModel):
    """報告書発信元設定更新リクエスト"""
    sender_organization: Optional[str] = Field(None, max_length=100, description="発信元所属（例：県立浦和高校サッカー部）")
    sender_name: Optional[str] = Field(None, max_length=100, description="発信元氏名（例：森川大地）")
    sender_contact: Optional[str] = Field(None, max_length=100, description="発信元連絡先（例：090-XXXX-XXXX）")


class SenderSettingsResponse(CamelCaseModel):
    """報告書発信元設定レスポンス"""
    sender_organization: Optional[str] = None
    sender_name: Optional[str] = None
    sender_contact: Optional[str] = None


class ReportRecipientResponse(ReportRecipientBase):
    """報告書送信先レスポンス"""
    id: int
    tournament_id: int
    created_at: datetime


class ReportParams(CamelCaseModel):
    """報告書出力パラメータ"""
    tournament_id: int = Field(..., description="大会ID")
    date: str = Field(..., description="日付（YYYY-MM-DD）")
    venue_id: Optional[int] = Field(None, description="会場ID")
    format: Literal["pdf", "excel"] = Field(..., description="出力形式")


class GoalReport(CamelCaseModel):
    """得点報告（報告書用）"""
    minute: int
    half: Literal[1, 2]
    team_name: str
    player_name: str
    display_text: str = Field(..., description="表示テキスト（例: '前半15分 浦和南 山田'）")


class MatchReport(CamelCaseModel):
    """試合報告書（1試合分）"""
    match_number: int
    kickoff_time: str
    home_team_name: str
    away_team_name: str
    score_half1: str = Field(..., description="前半スコア（例: '1-0'）")
    score_half2: str = Field(..., description="後半スコア（例: '2-1'）")
    score_total: str = Field(..., description="合計スコア（例: '3-1'）")
    score_pk: Optional[str] = Field(None, description="PKスコア（例: '5-4'）")
    goals: list[GoalReport] = []


class ReportData(CamelCaseModel):
    """報告書データ"""
    tournament: "TournamentResponse"
    date: str
    venue: Optional["VenueResponse"] = None
    matches: list["MatchWithDetails"]
    recipients: list[ReportRecipientResponse]
    generated_at: str
    generated_by: str


# 循環参照解決用のインポート
from .tournament import TournamentResponse
from .venue import VenueResponse
from .match import MatchWithDetails

ReportData.model_rebuild()
