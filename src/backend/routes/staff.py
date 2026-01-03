"""
Staff（スタッフ）ルーター
スタッフのCRUD操作を提供

仕様書: D:/UrawaCup/Requirement/PlayerManagement_Module_Spec.md
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.staff import Staff
from models.team import Team
from schemas.staff import (
    StaffCreate,
    StaffUpdate,
    StaffResponse,
    StaffList,
)

router = APIRouter()


@router.get("/", response_model=StaffList)
def get_staff_list(
    team_id: Optional[int] = Query(None, description="チームIDでフィルタ"),
    tournament_id: Optional[int] = Query(None, description="大会IDでフィルタ"),
    role: Optional[str] = Query(None, description="役割でフィルタ"),
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    db: Session = Depends(get_db),
):
    """スタッフ一覧を取得"""
    query = db.query(Staff)

    if team_id:
        query = query.filter(Staff.team_id == team_id)
    elif tournament_id:
        query = query.join(Team).filter(Team.tournament_id == tournament_id)

    if role:
        query = query.filter(Staff.role == role)

    total = query.count()
    staff_list = (
        query.order_by(Staff.team_id, Staff.is_primary.desc(), Staff.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return StaffList(staff=staff_list, total=total)


@router.get("/{staff_id}", response_model=StaffResponse)
def get_staff(
    staff_id: int,
    db: Session = Depends(get_db),
):
    """スタッフ詳細を取得"""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"スタッフが見つかりません (ID: {staff_id})"
        )
    return staff


@router.post("/", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    staff_data: StaffCreate,
    db: Session = Depends(get_db),
):
    """新規スタッフを登録"""
    # チームの存在確認
    team = db.query(Team).filter(Team.id == staff_data.team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"チームが見つかりません (ID: {staff_data.team_id})"
        )

    staff = Staff(**staff_data.model_dump(by_alias=False))
    db.add(staff)
    db.commit()
    db.refresh(staff)

    return staff


@router.put("/{staff_id}", response_model=StaffResponse)
def update_staff(
    staff_id: int,
    staff_data: StaffUpdate,
    db: Session = Depends(get_db),
):
    """スタッフ情報を更新"""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"スタッフが見つかりません (ID: {staff_id})"
        )

    update_data = staff_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(staff, field, value)

    db.commit()
    db.refresh(staff)

    return staff


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff(
    staff_id: int,
    db: Session = Depends(get_db),
):
    """スタッフを削除"""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"スタッフが見つかりません (ID: {staff_id})"
        )

    db.delete(staff)
    db.commit()

    return None


@router.get("/team/{team_id}", response_model=StaffList)
def get_staff_by_team(
    team_id: int,
    db: Session = Depends(get_db),
):
    """チーム別スタッフ一覧を取得"""
    # チームの存在確認
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"チームが見つかりません (ID: {team_id})"
        )

    staff_list = (
        db.query(Staff)
        .filter(Staff.team_id == team_id)
        .order_by(Staff.is_primary.desc(), Staff.id)
        .all()
    )

    return StaffList(staff=staff_list, total=len(staff_list))
