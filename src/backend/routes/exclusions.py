"""
ExclusionPair（対戦除外設定）ルーター
変則リーグの対戦除外設定を管理
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.exclusion_pair import ExclusionPair
from models.tournament import Tournament
from models.team import Team
from schemas.exclusion import (
    ExclusionPairCreate,
    ExclusionPairResponse,
    GroupExclusions,
)

router = APIRouter()


@router.get("/", response_model=List[ExclusionPairResponse])
def get_exclusions(
    tournament_id: int = Query(..., description="大会ID"),
    group_id: str = Query(None, pattern="^[A-D]$", description="グループでフィルタ"),
    db: Session = Depends(get_db),
):
    """対戦除外設定一覧を取得"""
    query = db.query(ExclusionPair).filter(ExclusionPair.tournament_id == tournament_id)

    if group_id:
        query = query.filter(ExclusionPair.group_id == group_id)

    return query.order_by(ExclusionPair.group_id, ExclusionPair.id).all()


@router.get("/by-group", response_model=List[GroupExclusions])
def get_exclusions_by_group(
    tournament_id: int = Query(..., description="大会ID"),
    db: Session = Depends(get_db),
):
    """
    グループごとの除外設定を取得

    各グループの除外設定と完了状態を返す
    """
    result = []

    for group_id in ["A", "B", "C", "D"]:
        # このグループの除外設定を取得
        exclusions = db.query(ExclusionPair).filter(
            ExclusionPair.tournament_id == tournament_id,
            ExclusionPair.group_id == group_id,
        ).all()

        # 各チームの除外数をカウント
        team_exclusion_count = {}
        for ex in exclusions:
            team_exclusion_count[ex.team1_id] = team_exclusion_count.get(ex.team1_id, 0) + 1
            team_exclusion_count[ex.team2_id] = team_exclusion_count.get(ex.team2_id, 0) + 1

        # このグループのチーム数を取得
        team_count = db.query(Team).filter(
            Team.tournament_id == tournament_id,
            Team.group_id == group_id,
        ).count()

        # 設定完了チェック（全チームが2チームを除外設定済み）
        is_complete = False
        if team_count == 6:
            # 6チームの場合、各チームが2つずつ除外されていれば完了
            # 除外ペアは6つ（6チーム×2除外÷2）
            is_complete = len(exclusions) == 6 and all(
                count == 2 for count in team_exclusion_count.values()
            )

        result.append(GroupExclusions(
            group_id=group_id,
            exclusions=exclusions,
            team_exclusion_count=team_exclusion_count,
            is_complete=is_complete,
        ))

    return result


@router.post("/", response_model=ExclusionPairResponse, status_code=status.HTTP_201_CREATED)
def create_exclusion(
    exclusion_data: ExclusionPairCreate,
    db: Session = Depends(get_db),
):
    """
    対戦除外設定を追加

    同一ペアの重複登録はエラー
    """
    # 大会の存在確認
    tournament = db.query(Tournament).filter(Tournament.id == exclusion_data.tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {exclusion_data.tournament_id})"
        )

    # チームの存在確認
    team1 = db.query(Team).filter(Team.id == exclusion_data.team1_id).first()
    team2 = db.query(Team).filter(Team.id == exclusion_data.team2_id).first()
    if not team1 or not team2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたチームが見つかりません"
        )

    # 同一チーム同士の除外は不可
    if exclusion_data.team1_id == exclusion_data.team2_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="同一チームを除外設定することはできません"
        )

    # 同一グループのチームであることを確認
    if team1.group_id != exclusion_data.group_id or team2.group_id != exclusion_data.group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="両チームが指定されたグループに所属している必要があります"
        )

    # 重複チェック（team1とteam2の順序を考慮）
    existing = db.query(ExclusionPair).filter(
        ExclusionPair.tournament_id == exclusion_data.tournament_id,
        ExclusionPair.group_id == exclusion_data.group_id,
        (
            ((ExclusionPair.team1_id == exclusion_data.team1_id) & (ExclusionPair.team2_id == exclusion_data.team2_id)) |
            ((ExclusionPair.team1_id == exclusion_data.team2_id) & (ExclusionPair.team2_id == exclusion_data.team1_id))
        ),
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このペアは既に除外設定されています"
        )

    # 各チームの除外数チェック（最大2チームまで）
    for team_id in [exclusion_data.team1_id, exclusion_data.team2_id]:
        count = db.query(ExclusionPair).filter(
            ExclusionPair.tournament_id == exclusion_data.tournament_id,
            ExclusionPair.group_id == exclusion_data.group_id,
            (ExclusionPair.team1_id == team_id) | (ExclusionPair.team2_id == team_id),
        ).count()
        if count >= 2:
            team = db.query(Team).filter(Team.id == team_id).first()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{team.name}は既に2チームとの対戦が除外されています"
            )

    exclusion = ExclusionPair(**exclusion_data.model_dump(by_alias=False))
    db.add(exclusion)
    db.commit()
    db.refresh(exclusion)

    return exclusion


@router.delete("/{exclusion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exclusion(
    exclusion_id: int,
    db: Session = Depends(get_db),
):
    """対戦除外設定を削除"""
    exclusion = db.query(ExclusionPair).filter(ExclusionPair.id == exclusion_id).first()
    if not exclusion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"除外設定が見つかりません (ID: {exclusion_id})"
        )

    db.delete(exclusion)
    db.commit()

    return None


@router.delete("/group/{tournament_id}/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_exclusions(
    tournament_id: int,
    group_id: str,
    db: Session = Depends(get_db),
):
    """グループの除外設定を全て削除"""
    db.query(ExclusionPair).filter(
        ExclusionPair.tournament_id == tournament_id,
        ExclusionPair.group_id == group_id,
    ).delete()

    db.commit()

    return None


@router.post("/auto-suggest/{tournament_id}/{group_id}", response_model=List[ExclusionPairResponse])
def suggest_exclusions(
    tournament_id: int,
    group_id: str,
    db: Session = Depends(get_db),
):
    """
    除外設定を自動提案

    地元チーム同士の対戦を避けるルールに基づいて提案
    実際の登録は行わない（提案のみ）
    """
    # グループのチームを取得
    teams = db.query(Team).filter(
        Team.tournament_id == tournament_id,
        Team.group_id == group_id,
    ).order_by(Team.group_order).all()

    if len(teams) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"グループ{group_id}のチーム数が6チームではありません"
        )

    # 地元チームを特定
    local_teams = [t for t in teams if t.team_type.value == "local"]

    suggestions = []

    # 地元チームが3チーム以上いる場合は、地元同士を除外
    if len(local_teams) >= 2:
        for i, t1 in enumerate(local_teams):
            for t2 in local_teams[i + 1:]:
                if len(suggestions) < 6:
                    suggestions.append(ExclusionPairResponse(
                        id=0,
                        tournament_id=tournament_id,
                        group_id=group_id,
                        team1_id=t1.id,
                        team2_id=t2.id,
                        reason="地元チーム同士",
                        created_at=None,
                    ))

    # 足りない分は招待チーム間で調整
    # （実際の運用ではより複雑なロジックが必要）

    return suggestions
