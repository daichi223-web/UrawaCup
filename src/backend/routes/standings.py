"""
Standing（順位表）ルーター
順位表の取得と更新を提供
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.standing import Standing
from models.team import Team
from models.group import Group
from models.tournament import Tournament
from schemas.standing import (
    StandingResponse,
    StandingWithTeam,
    GroupStanding,
    HeadToHead,
)
from schemas.group import GroupResponse

router = APIRouter()


@router.get("/", response_model=List[StandingWithTeam])
def get_standings(
    tournament_id: int = Query(..., description="大会ID"),
    group_id: Optional[str] = Query(None, pattern="^[A-D]$", description="グループでフィルタ"),
    db: Session = Depends(get_db),
):
    """
    順位表を取得

    グループを指定しない場合は全グループの順位表を返す
    """
    query = (
        db.query(Standing)
        .options(joinedload(Standing.team))
        .filter(Standing.tournament_id == tournament_id)
    )

    if group_id:
        query = query.filter(Standing.group_id == group_id)

    standings = query.order_by(Standing.group_id, Standing.rank).all()

    return standings


@router.get("/by-group", response_model=List[GroupStanding])
def get_standings_by_group(
    tournament_id: int = Query(..., description="大会ID"),
    db: Session = Depends(get_db),
):
    """グループごとにまとめた順位表を取得"""
    groups = (
        db.query(Group)
        .filter(Group.tournament_id == tournament_id)
        .order_by(Group.id)
        .all()
    )

    result = []
    for group in groups:
        standings = (
            db.query(Standing)
            .options(joinedload(Standing.team))
            .filter(
                Standing.tournament_id == tournament_id,
                Standing.group_id == group.id,
            )
            .order_by(Standing.rank)
            .all()
        )

        result.append(GroupStanding(
            group=GroupResponse.model_validate(group),
            standings=standings,
        ))

    return result


@router.get("/group/{group_id}", response_model=GroupStanding)
def get_group_standing(
    group_id: str,
    tournament_id: int = Query(..., description="大会ID"),
    db: Session = Depends(get_db),
):
    """特定グループの順位表を取得"""
    group = db.query(Group).filter(
        Group.id == group_id,
        Group.tournament_id == tournament_id,
    ).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"グループが見つかりません (ID: {group_id})"
        )

    standings = (
        db.query(Standing)
        .options(joinedload(Standing.team))
        .filter(
            Standing.tournament_id == tournament_id,
            Standing.group_id == group_id,
        )
        .order_by(Standing.rank)
        .all()
    )

    return GroupStanding(
        group=GroupResponse.model_validate(group),
        standings=standings,
    )


@router.post("/recalculate/{tournament_id}", response_model=List[GroupStanding])
def recalculate_standings(
    tournament_id: int,
    group_id: Optional[str] = Query(None, pattern="^[A-D]$", description="特定グループのみ再計算"),
    db: Session = Depends(get_db),
):
    """
    順位表を再計算

    試合結果に基づいて順位表を再計算する。
    通常は試合結果入力時に自動更新されるが、
    手動で再計算が必要な場合に使用。
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    from services.standing_service import StandingService
    standing_service = StandingService(db)

    if group_id:
        standing_service.update_group_standings(tournament_id, group_id)
        groups = [db.query(Group).filter(Group.id == group_id, Group.tournament_id == tournament_id).first()]
    else:
        for gid in ["A", "B", "C", "D"]:
            standing_service.update_group_standings(tournament_id, gid)
        groups = db.query(Group).filter(Group.tournament_id == tournament_id).order_by(Group.id).all()

    result = []
    for group in groups:
        if group:
            standings = (
                db.query(Standing)
                .options(joinedload(Standing.team))
                .filter(
                    Standing.tournament_id == tournament_id,
                    Standing.group_id == group.id,
                )
                .order_by(Standing.rank)
                .all()
            )

            result.append(GroupStanding(
                group=GroupResponse.model_validate(group),
                standings=standings,
            ))

    return result


@router.get("/head-to-head", response_model=HeadToHead)
def get_head_to_head(
    tournament_id: int = Query(..., description="大会ID"),
    team1_id: int = Query(..., description="チーム1 ID"),
    team2_id: int = Query(..., description="チーム2 ID"),
    db: Session = Depends(get_db),
):
    """
    2チーム間の直接対決成績を取得

    同勝点時の順位決定に使用
    """
    from models.match import Match, MatchStatus, MatchResult

    matches = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.status == MatchStatus.COMPLETED,
        (
            ((Match.home_team_id == team1_id) & (Match.away_team_id == team2_id)) |
            ((Match.home_team_id == team2_id) & (Match.away_team_id == team1_id))
        ),
    ).all()

    result = HeadToHead(
        team1_id=team1_id,
        team2_id=team2_id,
    )

    for match in matches:
        if match.home_team_id == team1_id:
            result.team1_goals += match.home_score_total or 0
            result.team2_goals += match.away_score_total or 0
            if match.result == MatchResult.HOME_WIN:
                result.team1_wins += 1
            elif match.result == MatchResult.AWAY_WIN:
                result.team2_wins += 1
            else:
                result.draws += 1
        else:
            result.team1_goals += match.away_score_total or 0
            result.team2_goals += match.home_score_total or 0
            if match.result == MatchResult.AWAY_WIN:
                result.team1_wins += 1
            elif match.result == MatchResult.HOME_WIN:
                result.team2_wins += 1
            else:
                result.draws += 1

    return result


@router.get("/top-scorers", response_model=List[dict])
def get_top_scorers(
    tournament_id: int = Query(..., description="大会ID"),
    limit: int = Query(10, ge=1, le=100, description="取得件数"),
    db: Session = Depends(get_db),
):
    """得点ランキングを取得（将来拡張用）"""
    from models.goal import Goal
    from models.match import Match, MatchStage
    from sqlalchemy import func

    # 研修試合を除く得点を集計
    scorers = (
        db.query(
            Goal.player_name,
            Goal.team_id,
            Team.name.label("team_name"),
            func.count(Goal.id).label("goals"),
        )
        .join(Match, Goal.match_id == Match.id)
        .join(Team, Goal.team_id == Team.id)
        .filter(
            Match.tournament_id == tournament_id,
            Match.stage != MatchStage.TRAINING,
            Goal.is_own_goal == False,
        )
        .group_by(Goal.player_name, Goal.team_id, Team.name)
        .order_by(func.count(Goal.id).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "rank": idx + 1,
            "player_name": s.player_name,
            "team_id": s.team_id,
            "team_name": s.team_name,
            "goals": s.goals,
        }
        for idx, s in enumerate(scorers)
    ]
