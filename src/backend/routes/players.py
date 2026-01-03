"""
Player（選手）ルーター
選手のCRUD操作とCSV/Excelインポートを提供

仕様書: D:/UrawaCup/Requirement/PlayerManagement_Module_Spec.md
"""

import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models.player import Player, normalize_name
from models.team import Team
from models.staff import Staff
from models.team_uniform import TeamUniform
from schemas.player import (
    PlayerCreate,
    PlayerUpdate,
    PlayerResponse,
    PlayerList,
    PlayerSuggestion,
    ImportPreviewResult,
    ImportResult,
    PlayerImportRow,
    StaffImportRow,
    UniformImportRow,
    ImportError as ImportErrorSchema,
    TeamInfoImport,
)
from services.player_import_service import (
    UrawaCupExcelParser,
    create_players_from_parse_result,
    create_staff_from_parse_result,
    create_uniforms_from_parse_result,
)

router = APIRouter()


@router.get("/", response_model=PlayerList)
def get_players(
    team_id: Optional[int] = Query(None, description="チームIDでフィルタ"),
    tournament_id: Optional[int] = Query(None, description="大会IDでフィルタ"),
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    db: Session = Depends(get_db),
):
    """選手一覧を取得"""
    query = db.query(Player)

    if team_id:
        query = query.filter(Player.team_id == team_id)
    elif tournament_id:
        # 大会IDでフィルタする場合はチームテーブルをjoin
        query = query.join(Team).filter(Team.tournament_id == tournament_id)

    total = query.count()
    players = (
        query.order_by(Player.team_id, Player.number)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return PlayerList(players=players, total=total)


@router.get("/suggest", response_model=List[PlayerSuggestion])
def suggest_players(
    team_id: int = Query(..., description="チームID"),
    q: Optional[str] = Query(None, description="検索クエリ（背番号または名前/フリガナ）"),
    db: Session = Depends(get_db),
):
    """
    得点者入力用の選手サジェスト（フロントエンド用）

    チームIDに所属する選手を検索し、入力補助に使用。
    背番号、名前、フリガナ（正規化済み）で検索可能。
    """
    return _get_player_suggestions(db, team_id, q)


@router.get("/suggestions/{team_id}", response_model=List[PlayerSuggestion])
def get_player_suggestions(
    team_id: int,
    q: Optional[str] = Query(None, description="検索クエリ（背番号または名前/フリガナ）"),
    db: Session = Depends(get_db),
):
    """
    得点者入力用の選手サジェスト（後方互換用）

    チームIDに所属する選手を検索し、入力補助に使用。
    背番号、名前、フリガナ（正規化済み）で検索可能。
    """
    return _get_player_suggestions(db, team_id, q)


def _get_player_suggestions(db: Session, team_id: int, q: Optional[str]) -> List[PlayerSuggestion]:
    """選手サジェストの共通ロジック"""
    query = db.query(Player).filter(
        Player.team_id == team_id,
        Player.is_active == True
    )

    if q:
        q = q.strip()
        # 背番号または名前で検索
        if q.isdigit():
            query = query.filter(Player.number == int(q))
        else:
            # 検索クエリを正規化
            normalized_q = normalize_name(q)
            # 名前、フリガナ、正規化名で部分一致検索
            query = query.filter(
                (Player.name.contains(q)) |
                (Player.name_kana.contains(q)) |
                (Player.name_normalized.contains(normalized_q))
            )

    players = query.order_by(Player.number).limit(20).all()

    return [PlayerSuggestion.from_player(p) for p in players]


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(
    player_id: int,
    db: Session = Depends(get_db),
):
    """選手詳細を取得"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"選手が見つかりません (ID: {player_id})"
        )
    return player


@router.post("/", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
def create_player(
    player_data: PlayerCreate,
    db: Session = Depends(get_db),
):
    """新規選手を登録"""
    # チームの存在確認
    team = db.query(Team).filter(Team.id == player_data.team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"チームが見つかりません (ID: {player_data.team_id})"
        )

    # 背番号重複チェック（NULLの場合はスキップ）
    if player_data.number is not None:
        existing = db.query(Player).filter(
            Player.team_id == player_data.team_id,
            Player.number == player_data.number,
            Player.is_active == True,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"背番号{player_data.number}は既に{existing.name}が使用しています"
            )

    player = Player(**player_data.model_dump(by_alias=False))
    # 正規化名を設定
    player.update_normalized_name()

    db.add(player)
    db.commit()
    db.refresh(player)

    return player


@router.put("/{player_id}", response_model=PlayerResponse)
def update_player(
    player_id: int,
    player_data: PlayerUpdate,
    db: Session = Depends(get_db),
):
    """選手情報を更新"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"選手が見つかりません (ID: {player_id})"
        )

    update_data = player_data.model_dump(exclude_unset=True)

    # 背番号変更時の重複チェック（NULLの場合はスキップ）
    if "number" in update_data and update_data["number"] is not None:
        existing = db.query(Player).filter(
            Player.team_id == player.team_id,
            Player.number == update_data["number"],
            Player.id != player_id,
            Player.is_active == True,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"背番号{update_data['number']}は既に{existing.name}が使用しています"
            )

    for field, value in update_data.items():
        setattr(player, field, value)

    # 名前またはフリガナが変更された場合は正規化名も更新
    if "name" in update_data or "name_kana" in update_data:
        player.update_normalized_name()

    db.commit()
    db.refresh(player)

    return player


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(
    player_id: int,
    db: Session = Depends(get_db),
):
    """選手を削除"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"選手が見つかりません (ID: {player_id})"
        )

    db.delete(player)
    db.commit()

    return None


@router.post("/import-csv/{team_id}", response_model=PlayerList)
async def import_players_csv(
    team_id: int,
    file: UploadFile = File(..., description="CSVファイル"),
    replace_existing: bool = Query(False, description="既存選手を削除して入れ替え"),
    db: Session = Depends(get_db),
):
    """
    CSVから選手を一括インポート

    CSVフォーマット:
    - number: 背番号（必須、1-99）
    - name: 選手名（必須）
    - grade: 学年（1-3）
    - notes: 備考
    """
    # チームの存在確認
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"チームが見つかりません (ID: {team_id})"
        )

    # 既存選手を削除する場合
    if replace_existing:
        db.query(Player).filter(Player.team_id == team_id).delete()

    # ファイル読み込み
    try:
        content = await file.read()
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

    imported_players = []
    errors = []
    existing_numbers = set()

    # 既存の背番号を取得（入れ替えモードでない場合）
    if not replace_existing:
        for p in db.query(Player).filter(Player.team_id == team_id).all():
            existing_numbers.add(p.number)

    for row_num, row in enumerate(reader, start=2):
        try:
            number_str = row.get("number", "").strip()
            if not number_str:
                errors.append(f"行{row_num}: 背番号が空です")
                continue

            try:
                number = int(number_str)
            except ValueError:
                errors.append(f"行{row_num}: 背番号は数値で指定してください")
                continue

            if number < 1 or number > 99:
                errors.append(f"行{row_num}: 背番号は1-99の範囲で指定してください")
                continue

            if number in existing_numbers:
                errors.append(f"行{row_num}: 背番号{number}は既に使用されています")
                continue

            name = row.get("name", "").strip()
            if not name:
                errors.append(f"行{row_num}: 選手名が空です")
                continue

            grade_str = row.get("grade", "").strip()
            grade = None
            if grade_str:
                try:
                    grade = int(grade_str)
                    if grade < 1 or grade > 3:
                        errors.append(f"行{row_num}: 学年は1-3の範囲で指定してください")
                        continue
                except ValueError:
                    errors.append(f"行{row_num}: 学年は数値で指定してください")
                    continue

            player = Player(
                team_id=team_id,
                number=number,
                name=name,
                grade=grade,
                notes=row.get("notes", "").strip() or None,
            )
            db.add(player)
            imported_players.append(player)
            existing_numbers.add(number)

        except Exception as e:
            errors.append(f"行{row_num}: {str(e)}")

    if errors:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "インポートエラー", "errors": errors}
        )

    db.commit()

    for player in imported_players:
        db.refresh(player)

    return PlayerList(players=imported_players, total=len(imported_players))


@router.get("/export-csv/{team_id}")
def export_players_csv(
    team_id: int,
    db: Session = Depends(get_db),
):
    """選手をCSVでエクスポート"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"チームが見つかりません (ID: {team_id})"
        )

    players = (
        db.query(Player)
        .filter(Player.team_id == team_id)
        .order_by(Player.number)
        .all()
    )

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["number", "name", "grade", "notes"],
        extrasaction="ignore",
    )
    writer.writeheader()

    for player in players:
        writer.writerow({
            "number": player.number,
            "name": player.name,
            "grade": player.grade or "",
            "notes": player.notes or "",
        })

    output.seek(0)
    content = "\ufeff" + output.getvalue()

    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": f"attachment; filename=players_{team_id}_{team.name}.csv"
        }
    )


# ===== Excelインポート機能 =====

@router.post("/import-excel/{team_id}/preview", response_model=ImportPreviewResult)
async def preview_excel_import(
    team_id: int,
    file: UploadFile = File(..., description="Excelファイル (.xls, .xlsx)"),
    db: Session = Depends(get_db),
):
    """
    Excelファイルをプレビュー（実際のインポート前の確認）

    浦和カップ参加申込書形式に対応。
    選手、スタッフ、ユニフォーム情報を解析して返す。
    """
    # チームの存在確認
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"チームが見つかりません (ID: {team_id})"
        )

    # ファイル形式チェック
    if not file.filename or not file.filename.lower().endswith(('.xls', '.xlsx')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Excelファイル (.xls, .xlsx) を指定してください"
        )

    # ファイル読み込み
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ファイルの読み込みに失敗しました: {str(e)}"
        )

    # パース
    parser = UrawaCupExcelParser()
    parse_result = parser.parse(content, file.filename)

    # 既存の選手との重複チェック
    existing_numbers = set()
    for p in db.query(Player).filter(
        Player.team_id == team_id,
        Player.is_active == True
    ).all():
        if p.number:
            existing_numbers.add(p.number)

    # プレビュー結果を構築
    player_rows = []
    for parsed in parse_result.players:
        status_str = "new"
        errors = []

        # 背番号重複チェック
        if parsed.number and parsed.number in existing_numbers:
            status_str = "warning"
            errors.append(f"背番号{parsed.number}は既に使用されています")

        # 必須フィールドチェック
        if not parsed.name:
            status_str = "error"
            errors.append("氏名が空です")

        player_rows.append(PlayerImportRow(
            row_number=parsed.row_number,
            number=parsed.number,
            name=parsed.name,
            name_kana=parsed.name_kana,
            grade=parsed.grade,
            position=parsed.position,
            height=parsed.height,
            previous_team=parsed.previous_team,
            status=status_str,
            errors=errors,
        ))

    # スタッフ情報
    staff_rows = [
        StaffImportRow(
            role=s.role,
            name=s.name,
            phone=s.phone,
            email=s.email,
        )
        for s in parse_result.staff
    ]

    # ユニフォーム情報
    uniform_rows = [
        UniformImportRow(
            player_type=u.player_type,
            uniform_type=u.uniform_type,
            shirt_color=u.shirt_color,
            pants_color=u.pants_color,
            socks_color=u.socks_color,
        )
        for u in parse_result.uniforms
    ]

    # チーム情報
    team_info = None
    if parse_result.team_info:
        team_info = TeamInfoImport(
            name=parse_result.team_info.name,
            address=parse_result.team_info.address,
            tel=parse_result.team_info.tel,
            fax=parse_result.team_info.fax,
        )

    # エラー情報
    import_errors = [
        ImportErrorSchema(
            row=e.get("row", 0),
            field=e.get("field", ""),
            type=e.get("type", "error"),
            message=e.get("message", ""),
        )
        for e in parse_result.errors
    ]

    return ImportPreviewResult(
        format=parse_result.format,
        team_info=team_info,
        staff=staff_rows,
        uniforms=uniform_rows,
        players=player_rows,
        errors=import_errors,
    )


@router.post("/import-excel/{team_id}", response_model=ImportResult)
async def import_excel(
    team_id: int,
    file: UploadFile = File(..., description="Excelファイル (.xls, .xlsx)"),
    replace_existing: bool = Query(False, description="既存データを削除して入れ替え"),
    import_staff: bool = Query(True, description="スタッフもインポート"),
    import_uniforms: bool = Query(True, description="ユニフォームもインポート"),
    skip_warnings: bool = Query(True, description="警告があってもインポート"),
    db: Session = Depends(get_db),
):
    """
    Excelファイルから選手・スタッフ・ユニフォームをインポート

    浦和カップ参加申込書形式に対応。
    """
    # チームの存在確認
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"チームが見つかりません (ID: {team_id})"
        )

    # ファイル形式チェック
    if not file.filename or not file.filename.lower().endswith(('.xls', '.xlsx')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Excelファイル (.xls, .xlsx) を指定してください"
        )

    # ファイル読み込み
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ファイルの読み込みに失敗しました: {str(e)}"
        )

    # パース
    parser = UrawaCupExcelParser()
    parse_result = parser.parse(content, file.filename)

    if parse_result.errors and not skip_warnings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "パースエラー",
                "errors": [e.get("message", "") for e in parse_result.errors]
            }
        )

    # 既存データを削除する場合
    if replace_existing:
        db.query(Player).filter(Player.team_id == team_id).delete()
        if import_staff:
            db.query(Staff).filter(Staff.team_id == team_id).delete()
        if import_uniforms:
            db.query(TeamUniform).filter(TeamUniform.team_id == team_id).delete()

    imported_count = 0
    updated_count = 0
    skipped_count = 0
    all_errors = []

    # 選手をインポート
    existing_numbers = set()
    if not replace_existing:
        for p in db.query(Player).filter(
            Player.team_id == team_id,
            Player.is_active == True
        ).all():
            if p.number:
                existing_numbers.add(p.number)

    players, player_errors = create_players_from_parse_result(parse_result, team_id)
    all_errors.extend(player_errors)

    for player in players:
        if not player.name:
            skipped_count += 1
            continue

        # 背番号重複チェック
        if player.number and player.number in existing_numbers:
            if skip_warnings:
                # 背番号をNULLにして登録
                player.number = None
            else:
                skipped_count += 1
                all_errors.append({
                    "row": 0,
                    "field": "number",
                    "type": "warning",
                    "message": f"背番号{player.number}は既に使用されています"
                })
                continue

        if player.number:
            existing_numbers.add(player.number)

        db.add(player)
        imported_count += 1

    # スタッフをインポート
    if import_staff:
        staff_list, staff_errors = create_staff_from_parse_result(parse_result, team_id)
        all_errors.extend(staff_errors)
        for staff in staff_list:
            db.add(staff)

    # ユニフォームをインポート
    if import_uniforms:
        uniforms, uniform_errors = create_uniforms_from_parse_result(parse_result, team_id)
        all_errors.extend(uniform_errors)
        for uniform in uniforms:
            db.add(uniform)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"データベースへの保存に失敗しました: {str(e)}"
        )

    return ImportResult(
        imported=imported_count,
        updated=updated_count,
        skipped=skipped_count,
        errors=[
            ImportErrorSchema(
                row=e.get("row", 0),
                field=e.get("field", ""),
                type=e.get("type", "error"),
                message=e.get("message", ""),
            )
            for e in all_errors
        ]
    )
