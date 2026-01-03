"""
APIルーター集約
全てのエンドポイントをここで登録
"""

from fastapi import APIRouter

# メインルーター
api_router = APIRouter()

# 各機能のルーターをインポート・登録
from .auth import router as auth_router
from .tournaments import router as tournaments_router
from .teams import router as teams_router
from .players import router as players_router
from .staff import router as staff_router
from .venues import router as venues_router
from .matches import router as matches_router
from .standings import router as standings_router
from .reports import router as reports_router
from .reports_excel import router as reports_excel_router
from .exclusions import router as exclusions_router

# 認証ルート（優先度最高）
api_router.include_router(auth_router, prefix="/auth", tags=["認証"])
api_router.include_router(tournaments_router, prefix="/tournaments", tags=["大会管理"])
api_router.include_router(teams_router, prefix="/teams", tags=["チーム管理"])
api_router.include_router(players_router, prefix="/players", tags=["選手管理"])
api_router.include_router(staff_router, prefix="/staff", tags=["スタッフ管理"])
api_router.include_router(venues_router, prefix="/venues", tags=["会場管理"])
api_router.include_router(exclusions_router, prefix="/exclusions", tags=["対戦除外設定"])
api_router.include_router(matches_router, prefix="/matches", tags=["試合管理"])
api_router.include_router(standings_router, prefix="/standings", tags=["順位表"])
api_router.include_router(reports_router, prefix="/reports", tags=["報告書"])
api_router.include_router(reports_excel_router, prefix="/reports", tags=["報告書Excel"])


@api_router.get("/")
async def api_root():
    """API ルートエンドポイント"""
    return {
        "message": "浦和カップ API v1",
        "endpoints": {
            "tournaments": "/api/tournaments - 大会管理（CRUD、コピー）",
            "teams": "/api/teams - チーム管理（CRUD、CSVインポート/エクスポート）",
            "players": "/api/players - 選手管理（CRUD、CSVインポート/エクスポート、サジェスト）",
            "venues": "/api/venues - 会場管理（CRUD、デフォルト設定）",
            "exclusions": "/api/exclusions - 対戦除外設定（変則リーグ用）",
            "matches": "/api/matches - 試合管理（CRUD、日程生成、スコア入力、ロック）",
            "standings": "/api/standings - 順位表（取得、再計算、得点ランキング）",
            "reports": "/api/reports - 報告書（PDF/Excel出力、送信先管理）",
        },
    }
