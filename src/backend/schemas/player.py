"""
Player（選手）スキーマ

仕様書: D:/UrawaCup/Requirement/PlayerManagement_Module_Spec.md
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from .common import CamelCaseModel


class PlayerBase(CamelCaseModel):
    """選手基本情報"""
    number: Optional[int] = Field(None, ge=1, le=99, description="背番号（NULL許容）")
    name: str = Field(..., min_length=1, max_length=100, description="氏名")
    name_kana: Optional[str] = Field(None, max_length=100, description="フリガナ")
    grade: Optional[int] = Field(None, ge=1, le=3, description="学年（1-3）")
    position: Optional[str] = Field(None, pattern=r'^(GK|DF|MF|FW)$', description="ポジション")
    height: Optional[int] = Field(None, ge=100, le=220, description="身長(cm)")
    previous_team: Optional[str] = Field(None, max_length=100, description="前所属チーム")
    is_captain: bool = Field(False, description="キャプテン")
    notes: Optional[str] = Field(None, max_length=500, description="備考")


class PlayerCreate(PlayerBase):
    """選手作成リクエスト"""
    team_id: int = Field(..., description="チームID")


class PlayerUpdate(CamelCaseModel):
    """選手更新リクエスト"""
    number: Optional[int] = Field(None, ge=1, le=99)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    name_kana: Optional[str] = Field(None, max_length=100)
    grade: Optional[int] = Field(None, ge=1, le=3)
    position: Optional[str] = Field(None, pattern=r'^(GK|DF|MF|FW)$')
    height: Optional[int] = Field(None, ge=100, le=220)
    previous_team: Optional[str] = Field(None, max_length=100)
    is_captain: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)


class PlayerResponse(PlayerBase):
    """選手レスポンス"""
    id: int
    team_id: int
    name_normalized: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    # 集計値（オプション）
    goal_count: Optional[int] = None


class PlayerList(CamelCaseModel):
    """選手一覧"""
    players: list[PlayerResponse]
    total: int


class PlayerSuggestion(CamelCaseModel):
    """選手サジェスト用（得点者入力）"""
    id: int
    team_id: int
    number: Optional[int] = None
    name: str
    name_kana: Optional[str] = None
    position: Optional[str] = None
    grade: Optional[int] = None
    display_text: str = Field(..., description="表示テキスト（例: '10 山田太郎'）")

    @classmethod
    def from_player(cls, player):
        """Playerモデルからサジェスト用データを作成"""
        number_str = str(player.number) if player.number else '-'
        return cls(
            id=player.id,
            team_id=player.team_id,
            number=player.number,
            name=player.name,
            name_kana=player.name_kana,
            position=player.position,
            grade=player.grade,
            display_text=f"{number_str} {player.name}"
        )


# インポート関連のスキーマ
class PlayerImportRow(CamelCaseModel):
    """インポート行データ"""
    row_number: int
    number: Optional[int] = None
    name: str
    name_kana: Optional[str] = None
    grade: Optional[int] = None
    position: Optional[str] = None
    height: Optional[int] = None
    previous_team: Optional[str] = None
    status: str = Field(..., pattern=r'^(new|update|error|warning)$')
    errors: list[str] = []


class ImportError(CamelCaseModel):
    """インポートエラー"""
    row: int
    field: str
    type: str = Field(..., pattern=r'^(error|warning)$')
    message: str


class StaffImportRow(CamelCaseModel):
    """スタッフインポート行データ"""
    role: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None


class UniformImportRow(CamelCaseModel):
    """ユニフォームインポート行データ"""
    player_type: str = Field(..., pattern=r'^(GK|FP)$')
    uniform_type: str = Field(..., pattern=r'^(primary|secondary)$')
    shirt_color: Optional[str] = None
    pants_color: Optional[str] = None
    socks_color: Optional[str] = None


class TeamInfoImport(CamelCaseModel):
    """チーム情報インポートデータ"""
    name: Optional[str] = None
    address: Optional[str] = None
    tel: Optional[str] = None
    fax: Optional[str] = None


class ImportPreviewResult(CamelCaseModel):
    """インポートプレビュー結果"""
    format: str
    team_info: Optional[TeamInfoImport] = None
    staff: list[StaffImportRow] = []
    uniforms: list[UniformImportRow] = []
    players: list[PlayerImportRow] = []
    errors: list[ImportError] = []


class ImportResult(CamelCaseModel):
    """インポート結果"""
    imported: int
    updated: int
    skipped: int
    errors: list[ImportError] = []
