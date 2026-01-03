"""
Team（チーム）ルーター
チームのCRUD操作とCSVインポート/エクスポートを提供
"""

import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.team import Team, TeamType
from models.tournament import Tournament
from models.standing import Standing
from models.user import User
from schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamList,
    TeamWithDetails,
)
from utils.auth import require_admin

router = APIRouter()


@router.get("/", response_model=TeamList)
def get_teams(
    tournament_id: Optional[int] = Query(None, description="大会IDでフィルタ"),
    group_id: Optional[str] = Query(None, pattern="^[A-D]$", description="グループでフィルタ"),
    team_type: Optional[str] = Query(None, description="チーム区分でフィルタ (local/invited)"),
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    db: Session = Depends(get_db),
):
    """
    チーム一覧を取得

    - 大会ID、グループ、チーム区分でフィルタリングが可能
    """
    query = db.query(Team)

    if tournament_id:
        query = query.filter(Team.tournament_id == tournament_id)
    if group_id:
        query = query.filter(Team.group_id == group_id)
    if team_type:
        query = query.filter(Team.team_type == team_type)

    total = query.count()
    teams = (
        query.order_by(Team.group_id, Team.group_order, Team.name)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return TeamList(teams=teams, total=total)


@router.get("/{team_id}", response_model=TeamWithDetails)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
):
    """チーム詳細を取得（選手リスト含む）"""
    team = (
        db.query(Team)
        .options(joinedload(Team.players), joinedload(Team.group))
        .filter(Team.id == team_id)
        .first()
    )
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"チームが見つかりません (ID: {team_id})"
        )
    return team


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """新規チームを作成（管理者専用）"""
    # 大会の存在確認
    tournament = db.query(Tournament).filter(Tournament.id == team_data.tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {team_data.tournament_id})"
        )

    # グループ内の番号重複チェック
    if team_data.group_id and team_data.group_order:
        existing = db.query(Team).filter(
            Team.tournament_id == team_data.tournament_id,
            Team.group_id == team_data.group_id,
            Team.group_order == team_data.group_order,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"グループ{team_data.group_id}の{team_data.group_order}番は既に使用されています"
            )

    # 明示的にsnake_caseフィールドを使用してTeamを作成
    team = Team(
        name=team_data.name,
        short_name=team_data.short_name,
        team_type=team_data.team_type,
        is_venue_host=team_data.is_venue_host,
        group_id=team_data.group_id,
        group_order=team_data.group_order,
        prefecture=team_data.prefecture,
        notes=team_data.notes,
        tournament_id=team_data.tournament_id,
    )
    db.add(team)
    db.commit()
    db.refresh(team)

    # 順位表エントリを作成
    if team.group_id:
        standing = Standing(
            tournament_id=team.tournament_id,
            group_id=team.group_id,
            team_id=team.id,
            rank=team.group_order or 0,
        )
        db.add(standing)
        db.commit()

    return team


@router.put("/{team_id}", response_model=TeamResponse)
@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    team_data: TeamUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """チーム情報を更新（管理者専用）"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"チームが見つかりません (ID: {team_id})"
        )

    update_data = team_data.model_dump(exclude_unset=True)

    # グループ内の番号重複チェック
    new_group_id = update_data.get("group_id", team.group_id)
    new_group_order = update_data.get("group_order", team.group_order)
    if new_group_id and new_group_order:
        existing = db.query(Team).filter(
            Team.tournament_id == team.tournament_id,
            Team.group_id == new_group_id,
            Team.group_order == new_group_order,
            Team.id != team_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"グループ{new_group_id}の{new_group_order}番は既に使用されています"
            )

    for field, value in update_data.items():
        setattr(team, field, value)

    db.commit()
    db.refresh(team)

    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """チームを削除（管理者専用）"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"チームが見つかりません (ID: {team_id})"
        )

    db.delete(team)
    db.commit()

    return None


@router.post("/import-csv", response_model=TeamList)
async def import_teams_csv(
    tournament_id: int = Query(..., description="インポート先の大会ID"),
    file: UploadFile = File(..., description="CSVファイル"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    CSVからチームを一括インポート

    CSVフォーマット:
    - name: チーム名（必須）
    - short_name: 略称
    - team_type: local または invited（デフォルト: invited）
    - is_venue_host: true/false（デフォルト: false）
    - group_id: A/B/C/D
    - group_order: 1-6
    - prefecture: 都道府県
    - notes: 備考
    """
    # 大会の存在確認
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    # ファイル読み込み
    try:
        content = await file.read()
        # BOM付きUTF-8とShift_JISに対応
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            decoded = content.decode("shift_jis")

        reader = csv.DictReader(io.StringIO(decoded))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSVファイルの読み込みに失敗しました: {str(e)}"
        )

    imported_teams = []
    errors = []

    for row_num, row in enumerate(reader, start=2):  # ヘッダー行を1行目として
        try:
            name = row.get("name", "").strip()
            if not name:
                errors.append(f"行{row_num}: チーム名が空です")
                continue

            team_type = TeamType.INVITED
            type_str = row.get("team_type", "").strip().lower()
            if type_str == "local":
                team_type = TeamType.LOCAL

            is_venue_host = row.get("is_venue_host", "").strip().lower() in ("true", "1", "yes")

            group_id = row.get("group_id", "").strip().upper()
            if group_id and group_id not in "ABCD":
                errors.append(f"行{row_num}: 無効なグループID '{group_id}'")
                continue
            group_id = group_id if group_id else None

            group_order = row.get("group_order", "").strip()
            group_order = int(group_order) if group_order else None
            if group_order and (group_order < 1 or group_order > 6):
                errors.append(f"行{row_num}: グループ番号は1-6の範囲で指定してください")
                continue

            team = Team(
                tournament_id=tournament_id,
                name=name,
                short_name=row.get("short_name", "").strip() or None,
                team_type=team_type,
                is_venue_host=is_venue_host,
                group_id=group_id,
                group_order=group_order,
                prefecture=row.get("prefecture", "").strip() or None,
                notes=row.get("notes", "").strip() or None,
            )
            db.add(team)
            imported_teams.append(team)

        except Exception as e:
            errors.append(f"行{row_num}: {str(e)}")

    if errors:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "インポートエラー", "errors": errors}
        )

    db.commit()

    # 順位表エントリを作成
    for team in imported_teams:
        if team.group_id:
            standing = Standing(
                tournament_id=team.tournament_id,
                group_id=team.group_id,
                team_id=team.id,
                rank=team.group_order or 0,
            )
            db.add(standing)
    db.commit()

    # 再取得してレスポンス用に整形
    for team in imported_teams:
        db.refresh(team)

    return TeamList(teams=imported_teams, total=len(imported_teams))


@router.get("/export-csv/{tournament_id}")
def export_teams_csv(
    tournament_id: int,
    db: Session = Depends(get_db),
):
    """
    チームをCSVでエクスポート

    大会に所属する全チームをCSV形式でダウンロード
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    teams = (
        db.query(Team)
        .filter(Team.tournament_id == tournament_id)
        .order_by(Team.group_id, Team.group_order, Team.name)
        .all()
    )

    # CSV生成
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["name", "short_name", "team_type", "is_venue_host", "group_id", "group_order", "prefecture", "notes"],
        extrasaction="ignore",
    )
    writer.writeheader()

    for team in teams:
        writer.writerow({
            "name": team.name,
            "short_name": team.short_name or "",
            "team_type": team.team_type.value if team.team_type else "invited",
            "is_venue_host": "true" if team.is_venue_host else "false",
            "group_id": team.group_id or "",
            "group_order": team.group_order or "",
            "prefecture": team.prefecture or "",
            "notes": team.notes or "",
        })

    output.seek(0)

    # BOM付きUTF-8でエンコード（Excel対応）
    content = "\ufeff" + output.getvalue()

    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": f"attachment; filename=teams_{tournament_id}.csv"
        }
    )


@router.post("/{team_id}/assign-group", response_model=TeamResponse)
def assign_team_to_group(
    team_id: int,
    group_id: str = Query(..., pattern="^[A-D]$", description="グループID"),
    group_order: int = Query(..., ge=1, le=6, description="グループ内番号"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    チームをグループに割り当て（管理者専用）

    グループ分け時に使用。既存の割り当てがあれば上書き。
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"チームが見つかりません (ID: {team_id})"
        )

    # 番号重複チェック
    existing = db.query(Team).filter(
        Team.tournament_id == team.tournament_id,
        Team.group_id == group_id,
        Team.group_order == group_order,
        Team.id != team_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"グループ{group_id}の{group_order}番は既に{existing.name}が使用しています"
        )

    old_group_id = team.group_id

    team.group_id = group_id
    team.group_order = group_order

    # 順位表エントリを更新または作成
    standing = db.query(Standing).filter(
        Standing.tournament_id == team.tournament_id,
        Standing.team_id == team.id,
    ).first()

    if standing:
        standing.group_id = group_id
    else:
        standing = Standing(
            tournament_id=team.tournament_id,
            group_id=group_id,
            team_id=team.id,
            rank=group_order,
        )
        db.add(standing)

    db.commit()
    db.refresh(team)

    return team


@router.get("/template/csv")
def download_team_template():
    """
    チームCSVインポート用テンプレートをダウンロード

    テンプレートには以下の列が含まれます:
    - name: チーム名（必須）
    - short_name: 略称
    - team_type: local または invited（デフォルト: invited）
    - is_venue_host: true/false（デフォルト: false）
    - group_id: A/B/C/D
    - group_order: 1-6
    - prefecture: 都道府県
    - notes: 備考
    """
    from pathlib import Path

    template_path = Path(__file__).parent.parent / "templates" / "teams_import_template.csv"

    if not template_path.exists():
        # テンプレートファイルがない場合は動的に生成
        content = """name,short_name,team_type,is_venue_host,group_id,group_order,prefecture,notes
浦和南高校,浦和南,local,true,A,1,埼玉県,会場担当校
市立浦和高校,市浦和,local,true,B,1,埼玉県,会場担当校
浦和学院,浦和学,local,true,C,1,埼玉県,会場担当校
武南高校,武南,local,true,D,1,埼玉県,会場担当校
サンプル高校,サンプル,invited,false,A,2,東京都,
"""
    else:
        content = template_path.read_text(encoding="utf-8-sig")

    # BOM付きUTF-8でエンコード（Excel対応）
    content_with_bom = "\ufeff" + content if not content.startswith("\ufeff") else content

    return StreamingResponse(
        iter([content_with_bom]),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": "attachment; filename=teams_import_template.csv"
        }
    )
