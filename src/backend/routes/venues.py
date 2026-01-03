"""
Venue（会場）ルーター
会場のCRUD操作を提供
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.venue import Venue
from models.tournament import Tournament
from models.group import Group
from schemas.venue import (
    VenueCreate,
    VenueUpdate,
    VenueResponse,
    VenueList,
)

router = APIRouter()


@router.get("/", response_model=VenueList)
def get_venues(
    tournament_id: Optional[int] = Query(None, description="大会IDでフィルタ"),
    for_preliminary: Optional[bool] = Query(None, description="予選用会場のみ"),
    for_final_day: Optional[bool] = Query(None, description="最終日用会場のみ"),
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    db: Session = Depends(get_db),
):
    """会場一覧を取得"""
    query = db.query(Venue)

    if tournament_id:
        query = query.filter(Venue.tournament_id == tournament_id)
    if for_preliminary is not None:
        query = query.filter(Venue.for_preliminary == for_preliminary)
    if for_final_day is not None:
        query = query.filter(Venue.for_final_day == for_final_day)

    total = query.count()
    venues = query.order_by(Venue.group_id, Venue.name).offset(skip).limit(limit).all()

    return VenueList(venues=venues, total=total)


@router.get("/{venue_id}", response_model=VenueResponse)
def get_venue(
    venue_id: int,
    db: Session = Depends(get_db),
):
    """会場詳細を取得"""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会場が見つかりません (ID: {venue_id})"
        )
    return venue


@router.post("/", response_model=VenueResponse, status_code=status.HTTP_201_CREATED)
def create_venue(
    venue_data: VenueCreate,
    db: Session = Depends(get_db),
):
    """新規会場を作成"""
    # 大会の存在確認
    tournament = db.query(Tournament).filter(Tournament.id == venue_data.tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {venue_data.tournament_id})"
        )

    venue = Venue(**venue_data.model_dump(by_alias=False))
    db.add(venue)
    db.commit()
    db.refresh(venue)

    # グループとの紐付けを更新
    if venue.group_id:
        group = db.query(Group).filter(
            Group.id == venue.group_id,
            Group.tournament_id == venue.tournament_id,
        ).first()
        if group:
            group.venue_id = venue.id
            db.commit()

    return venue


@router.put("/{venue_id}", response_model=VenueResponse)
@router.patch("/{venue_id}", response_model=VenueResponse)
def update_venue(
    venue_id: int,
    venue_data: VenueUpdate,
    db: Session = Depends(get_db),
):
    """会場情報を更新（PUT/PATCH両対応）"""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会場が見つかりません (ID: {venue_id})"
        )

    update_data = venue_data.model_dump(exclude_unset=True)
    old_group_id = venue.group_id

    for field, value in update_data.items():
        setattr(venue, field, value)

    db.commit()
    db.refresh(venue)

    # グループとの紐付けを更新
    new_group_id = venue.group_id
    if old_group_id != new_group_id:
        # 旧グループの紐付けを解除
        if old_group_id:
            old_group = db.query(Group).filter(
                Group.id == old_group_id,
                Group.tournament_id == venue.tournament_id,
            ).first()
            if old_group and old_group.venue_id == venue.id:
                old_group.venue_id = None

        # 新グループに紐付け
        if new_group_id:
            new_group = db.query(Group).filter(
                Group.id == new_group_id,
                Group.tournament_id == venue.tournament_id,
            ).first()
            if new_group:
                new_group.venue_id = venue.id

        db.commit()

    return venue


@router.delete("/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_venue(
    venue_id: int,
    db: Session = Depends(get_db),
):
    """会場を削除"""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会場が見つかりません (ID: {venue_id})"
        )

    # グループとの紐付けを解除
    if venue.group_id:
        group = db.query(Group).filter(
            Group.id == venue.group_id,
            Group.tournament_id == venue.tournament_id,
        ).first()
        if group and group.venue_id == venue.id:
            group.venue_id = None
            db.commit()

    db.delete(venue)
    db.commit()

    return None


@router.post("/{tournament_id}/setup-default", response_model=VenueList)
def setup_default_venues(
    tournament_id: int,
    db: Session = Depends(get_db),
):
    """
    デフォルトの会場設定を作成

    浦和カップの標準会場:
    - 浦和南高G（Aグループ）
    - 市立浦和高G（Bグループ）
    - 浦和学院G（Cグループ）
    - 武南高G（Dグループ）
    - 駒場スタジアム（最終日1位リーグ）
    """
    # 大会の存在確認
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    # 既存の会場があるかチェック
    existing_count = db.query(Venue).filter(Venue.tournament_id == tournament_id).count()
    if existing_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="既に会場が登録されています。初期化する場合は既存の会場を削除してください。"
        )

    # デフォルト会場を作成
    default_venues = [
        {
            "name": "浦和南高G",
            "group_id": "A",
            "for_preliminary": True,
            "for_final_day": True,
            "max_matches_per_day": 6,
        },
        {
            "name": "市立浦和高G",
            "group_id": "B",
            "for_preliminary": True,
            "for_final_day": True,
            "max_matches_per_day": 6,
        },
        {
            "name": "浦和学院G",
            "group_id": "C",
            "for_preliminary": True,
            "for_final_day": True,
            "max_matches_per_day": 6,
        },
        {
            "name": "武南高G",
            "group_id": "D",
            "for_preliminary": True,
            "for_final_day": True,
            "max_matches_per_day": 6,
        },
        {
            "name": "駒場スタジアム",
            "group_id": None,
            "for_preliminary": False,
            "for_final_day": True,
            "max_matches_per_day": 4,
            "notes": "1位リーグ（準決勝〜決勝）会場",
        },
    ]

    created_venues = []
    for venue_data in default_venues:
        venue = Venue(
            tournament_id=tournament_id,
            **venue_data,
        )
        db.add(venue)
        created_venues.append(venue)

    db.flush()

    # グループとの紐付けを更新
    for venue in created_venues:
        if venue.group_id:
            group = db.query(Group).filter(
                Group.id == venue.group_id,
                Group.tournament_id == tournament_id,
            ).first()
            if group:
                group.venue_id = venue.id

    db.commit()

    for venue in created_venues:
        db.refresh(venue)

    return VenueList(venues=created_venues, total=len(created_venues))
