"""
浦和カップ トーナメント管理システム - Pydanticスキーマ

APIリクエスト/レスポンスのバリデーション用
"""

from .tournament import (
    TournamentBase, TournamentCreate, TournamentUpdate, TournamentResponse, TournamentList
)
from .team import (
    TeamBase, TeamCreate, TeamUpdate, TeamResponse, TeamList, TeamWithDetails
)
from .player import (
    PlayerBase, PlayerCreate, PlayerUpdate, PlayerResponse, PlayerList, PlayerSuggestion,
    PlayerImportRow, ImportError, ImportPreviewResult, ImportResult,
    StaffImportRow, UniformImportRow, TeamInfoImport
)
from .staff import (
    StaffBase, StaffCreate, StaffUpdate, StaffResponse, StaffList
)
from .team_uniform import (
    TeamUniformBase, TeamUniformCreate, TeamUniformUpdate, TeamUniformResponse, TeamUniformList
)
from .group import (
    GroupBase, GroupCreate, GroupResponse, GroupWithDetails
)
from .venue import (
    VenueBase, VenueCreate, VenueUpdate, VenueResponse, VenueList
)
from .match import (
    MatchBase, MatchCreate, MatchUpdate, MatchScoreInput, MatchResponse, MatchWithDetails, MatchList
)
from .goal import (
    GoalBase, GoalCreate, GoalUpdate, GoalInput, GoalResponse, GoalDetail
)
from .standing import (
    StandingBase, StandingResponse, StandingWithTeam, GroupStanding, HeadToHead
)
from .user import (
    UserBase, UserCreate, UserResponse, LoginRequest, LoginResponse, AuthUser
)
from .report import (
    ReportRecipientBase, ReportRecipientCreate, ReportRecipientResponse,
    ReportParams, ReportData, MatchReport, GoalReport
)
from .exclusion import (
    ExclusionPairBase, ExclusionPairCreate, ExclusionPairResponse, GroupExclusions
)
from .common import (
    ApiResponse, ApiErrorResponse, PaginationParams, PaginatedResponse
)

__all__ = [
    # Tournament
    "TournamentBase", "TournamentCreate", "TournamentUpdate", "TournamentResponse", "TournamentList",
    # Team
    "TeamBase", "TeamCreate", "TeamUpdate", "TeamResponse", "TeamList", "TeamWithDetails",
    # Player
    "PlayerBase", "PlayerCreate", "PlayerUpdate", "PlayerResponse", "PlayerList", "PlayerSuggestion",
    "PlayerImportRow", "ImportError", "ImportPreviewResult", "ImportResult",
    "StaffImportRow", "UniformImportRow", "TeamInfoImport",
    # Staff
    "StaffBase", "StaffCreate", "StaffUpdate", "StaffResponse", "StaffList",
    # TeamUniform
    "TeamUniformBase", "TeamUniformCreate", "TeamUniformUpdate", "TeamUniformResponse", "TeamUniformList",
    # Group
    "GroupBase", "GroupCreate", "GroupResponse", "GroupWithDetails",
    # Venue
    "VenueBase", "VenueCreate", "VenueUpdate", "VenueResponse", "VenueList",
    # Match
    "MatchBase", "MatchCreate", "MatchUpdate", "MatchScoreInput", "MatchResponse", "MatchWithDetails", "MatchList",
    # Goal
    "GoalBase", "GoalCreate", "GoalUpdate", "GoalInput", "GoalResponse", "GoalDetail",
    # Standing
    "StandingBase", "StandingResponse", "StandingWithTeam", "GroupStanding", "HeadToHead",
    # User
    "UserBase", "UserCreate", "UserResponse", "LoginRequest", "LoginResponse", "AuthUser",
    # Report
    "ReportRecipientBase", "ReportRecipientCreate", "ReportRecipientResponse",
    "ReportParams", "ReportData", "MatchReport", "GoalReport",
    # Exclusion
    "ExclusionPairBase", "ExclusionPairCreate", "ExclusionPairResponse", "GroupExclusions",
    # Common
    "ApiResponse", "ApiErrorResponse", "PaginationParams", "PaginatedResponse",
]
