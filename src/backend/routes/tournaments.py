"""
Tournament（大会）ルーター
大会のCRUD操作を提供
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.tournament import Tournament
from models.group import Group
from models.user import User
from schemas.tournament import (
    TournamentCreate,
    TournamentUpdate,
    TournamentResponse,
    TournamentList,
)
from utils.auth import require_admin

router = APIRouter()


@router.get("/", response_model=TournamentList)
def get_tournaments(
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="開催年度でフィルタ"),
    db: Session = Depends(get_db),
):
    """
    大会一覧を取得

    - 年度でのフィルタリングが可能
    - 作成日時の降順でソート
    """
    query = db.query(Tournament)

    if year:
        query = query.filter(Tournament.year == year)

    total = query.count()
    tournaments = query.order_by(Tournament.created_at.desc()).offset(skip).limit(limit).all()

    return TournamentList(tournaments=tournaments, total=total)


@router.get("/{tournament_id}", response_model=TournamentResponse)
def get_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
):
    """大会詳細を取得"""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )
    return tournament


@router.post("/", response_model=TournamentResponse, status_code=status.HTTP_201_CREATED)
def create_tournament(
    tournament_data: TournamentCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    新規大会を作成（管理者専用）

    大会作成時に自動でグループ（A, B, C, D）も作成される
    """
    # 日付の妥当性チェック
    if tournament_data.end_date < tournament_data.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="終了日は開始日以降である必要があります"
        )

    # 大会を作成 - 明示的にsnake_caseフィールドを使用
    tournament = Tournament(
        name=tournament_data.name,
        edition=tournament_data.edition,
        year=tournament_data.year,
        start_date=tournament_data.start_date,
        end_date=tournament_data.end_date,
        match_duration=tournament_data.match_duration,
        half_duration=tournament_data.half_duration,
        interval_minutes=tournament_data.interval_minutes,
    )
    db.add(tournament)
    db.flush()  # IDを取得するためにflush

    # グループを自動作成（A, B, C, D）
    group_names = {
        "A": "Aグループ（浦和南G）",
        "B": "Bグループ（市立浦和G）",
        "C": "Cグループ（浦和学院G）",
        "D": "Dグループ（武南G）",
    }

    for group_id, group_name in group_names.items():
        group = Group(
            id=group_id,
            tournament_id=tournament.id,
            name=group_name,
        )
        db.add(group)

    db.commit()
    db.refresh(tournament)

    return tournament


@router.put("/{tournament_id}", response_model=TournamentResponse)
def update_tournament(
    tournament_id: int,
    tournament_data: TournamentUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """大会情報を更新（管理者専用）"""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    update_data = tournament_data.model_dump(exclude_unset=True)

    # 日付の妥当性チェック
    start_date = update_data.get("start_date", tournament.start_date)
    end_date = update_data.get("end_date", tournament.end_date)
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="終了日は開始日以降である必要があります"
        )

    for field, value in update_data.items():
        setattr(tournament, field, value)

    db.commit()
    db.refresh(tournament)

    return tournament


@router.delete("/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    大会を削除（管理者専用）

    関連するチーム、試合、順位表なども全て削除される（カスケード削除）
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    db.delete(tournament)
    db.commit()

    return None


@router.post("/{tournament_id}/copy", response_model=TournamentResponse, status_code=status.HTTP_201_CREATED)
def copy_tournament(
    tournament_id: int,
    new_year: int = Query(..., ge=2000, le=2100, description="新しい開催年度"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    既存大会から新規大会を複製（管理者専用）

    - 基本情報をコピー
    - グループ構成をコピー
    - チームリストはコピーしない（招待チームが毎年変わるため）
    """
    source = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"コピー元の大会が見つかりません (ID: {tournament_id})"
        )

    # 新しい大会を作成
    new_tournament = Tournament(
        name=source.name,
        edition=source.edition + 1,
        year=new_year,
        start_date=source.start_date.replace(year=new_year),
        end_date=source.end_date.replace(year=new_year),
        match_duration=source.match_duration,
        half_duration=source.half_duration,
        interval_minutes=source.interval_minutes,
    )
    db.add(new_tournament)
    db.flush()

    # グループをコピー
    for source_group in source.groups:
        new_group = Group(
            id=source_group.id,
            tournament_id=new_tournament.id,
            name=source_group.name,
        )
        db.add(new_group)

    db.commit()
    db.refresh(new_tournament)

    return new_tournament
