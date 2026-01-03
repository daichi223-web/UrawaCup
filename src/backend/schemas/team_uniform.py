"""
TeamUniform（チームユニフォーム）スキーマ

仕様書: D:/UrawaCup/Requirement/PlayerManagement_Module_Spec.md
"""

from typing import Optional
from pydantic import Field

from .common import CamelCaseModel


class TeamUniformBase(CamelCaseModel):
    """ユニフォーム基本情報"""
    player_type: str = Field(..., pattern=r'^(GK|FP)$', description="GK / FP")
    uniform_type: str = Field(..., pattern=r'^(primary|secondary)$', description="primary / secondary")
    shirt_color: Optional[str] = Field(None, max_length=50, description="シャツの色")
    pants_color: Optional[str] = Field(None, max_length=50, description="パンツの色")
    socks_color: Optional[str] = Field(None, max_length=50, description="ストッキングの色")


class TeamUniformCreate(TeamUniformBase):
    """ユニフォーム作成リクエスト"""
    team_id: int = Field(..., description="チームID")


class TeamUniformUpdate(CamelCaseModel):
    """ユニフォーム更新リクエスト"""
    shirt_color: Optional[str] = Field(None, max_length=50)
    pants_color: Optional[str] = Field(None, max_length=50)
    socks_color: Optional[str] = Field(None, max_length=50)


class TeamUniformResponse(TeamUniformBase):
    """ユニフォームレスポンス"""
    id: int
    team_id: int


class TeamUniformList(CamelCaseModel):
    """ユニフォーム一覧"""
    uniforms: list[TeamUniformResponse]
    total: int
