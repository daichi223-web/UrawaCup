"""
Reports（報告書）ルーター
報告書の生成とPDF/Excelエクスポートを提供
"""

import io
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.tournament import Tournament
from models.match import Match, MatchStage, MatchStatus
from models.venue import Venue
from models.goal import Goal
from models.report_recipient import ReportRecipient
from schemas.report import (
    ReportRecipientCreate,
    ReportRecipientResponse,
    ReportParams,
    MatchReport,
    GoalReport,
    ReportData,
    SenderSettingsUpdate,
    SenderSettingsResponse,
)

router = APIRouter()


# ================== 報告書送信先管理 ==================

@router.get("/recipients", response_model=List[ReportRecipientResponse])
def get_recipients(
    tournament_id: int = Query(..., description="大会ID"),
    db: Session = Depends(get_db),
):
    """報告書送信先一覧を取得"""
    recipients = db.query(ReportRecipient).filter(
        ReportRecipient.tournament_id == tournament_id
    ).all()
    return recipients


@router.post("/recipients", response_model=ReportRecipientResponse, status_code=status.HTTP_201_CREATED)
def create_recipient(
    recipient_data: ReportRecipientCreate,
    db: Session = Depends(get_db),
):
    """報告書送信先を追加"""
    tournament = db.query(Tournament).filter(Tournament.id == recipient_data.tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {recipient_data.tournament_id})"
        )

    recipient = ReportRecipient(**recipient_data.model_dump(by_alias=False))
    db.add(recipient)
    db.commit()
    db.refresh(recipient)

    return recipient


@router.delete("/recipients/{recipient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipient(
    recipient_id: int,
    db: Session = Depends(get_db),
):
    """報告書送信先を削除"""
    recipient = db.query(ReportRecipient).filter(ReportRecipient.id == recipient_id).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"送信先が見つかりません (ID: {recipient_id})"
        )

    db.delete(recipient)
    db.commit()

    return None


@router.post("/recipients/{tournament_id}/setup-default", response_model=List[ReportRecipientResponse])
def setup_default_recipients(
    tournament_id: int,
    db: Session = Depends(get_db),
):
    """
    デフォルトの送信先を設定

    - 埼玉新聞
    - テレビ埼玉
    - イシクラ
    - 埼玉県サッカー協会
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    default_recipients = [
        {"name": "埼玉新聞", "notes": "スポーツ部"},
        {"name": "テレビ埼玉", "notes": "報道部"},
        {"name": "イシクラ", "notes": ""},
        {"name": "埼玉県サッカー協会", "notes": ""},
    ]

    created = []
    for data in default_recipients:
        recipient = ReportRecipient(
            tournament_id=tournament_id,
            **data,
        )
        db.add(recipient)
        created.append(recipient)

    db.commit()

    for r in created:
        db.refresh(r)

    return created


# ================== 報告書発信元設定 ==================
# 要件準拠パス: GET/PUT /tournaments/{id}/report-settings

@router.get("/tournaments/{tournament_id}/report-settings", response_model=SenderSettingsResponse)
@router.get("/sender-settings/{tournament_id}", response_model=SenderSettingsResponse, include_in_schema=False)
def get_sender_settings(
    tournament_id: int,
    db: Session = Depends(get_db),
):
    """
    報告書発信元設定を取得

    要件準拠パス: GET /tournaments/{id}/report-settings
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    return SenderSettingsResponse(
        sender_organization=tournament.sender_organization,
        sender_name=tournament.sender_name,
        sender_contact=tournament.sender_contact,
    )


@router.put("/tournaments/{tournament_id}/report-settings", response_model=SenderSettingsResponse)
@router.patch("/sender-settings/{tournament_id}", response_model=SenderSettingsResponse, include_in_schema=False)
def update_sender_settings(
    tournament_id: int,
    settings: SenderSettingsUpdate,
    db: Session = Depends(get_db),
):
    """
    報告書発信元設定を更新

    要件準拠パス: PUT /tournaments/{id}/report-settings
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    # 値が指定されたフィールドのみ更新
    update_data = settings.model_dump(by_alias=False, exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(tournament, field):
            setattr(tournament, field, value)

    db.commit()
    db.refresh(tournament)

    return SenderSettingsResponse(
        sender_organization=tournament.sender_organization,
        sender_name=tournament.sender_name,
        sender_contact=tournament.sender_contact,
    )


# ================== 報告書データ取得 ==================

@router.get("/data", response_model=ReportData)
def get_report_data(
    tournament_id: int = Query(..., description="大会ID"),
    target_date: date = Query(..., description="対象日"),
    venue_id: Optional[int] = Query(None, description="会場ID（省略時は全会場）"),
    db: Session = Depends(get_db),
):
    """報告書用データを取得"""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    # 試合データを取得
    query = (
        db.query(Match)
        .options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            joinedload(Match.venue),
            joinedload(Match.group),
            joinedload(Match.goals),
        )
        .filter(
            Match.tournament_id == tournament_id,
            Match.match_date == target_date,
            Match.stage != MatchStage.TRAINING,  # 研修試合は報告書に含めない
        )
    )

    if venue_id:
        query = query.filter(Match.venue_id == venue_id)

    matches = query.order_by(Match.venue_id, Match.match_order).all()

    # 会場情報
    venue = None
    if venue_id:
        venue = db.query(Venue).filter(Venue.id == venue_id).first()

    # 送信先
    recipients = db.query(ReportRecipient).filter(
        ReportRecipient.tournament_id == tournament_id
    ).all()

    return ReportData(
        tournament=tournament,
        date=target_date.isoformat(),
        venue=venue,
        matches=matches,
        recipients=recipients,
        generated_at=datetime.now().isoformat(),
        generated_by="浦和カップ運営事務局",
    )


@router.get("/match-reports", response_model=List[MatchReport])
def get_match_reports(
    tournament_id: int = Query(..., description="大会ID"),
    target_date: date = Query(..., description="対象日"),
    venue_id: Optional[int] = Query(None, description="会場ID"),
    db: Session = Depends(get_db),
):
    """
    試合報告書形式でデータを取得

    報告書出力用に整形されたデータを返す
    """
    query = (
        db.query(Match)
        .options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            joinedload(Match.goals).joinedload(Goal.team),
        )
        .filter(
            Match.tournament_id == tournament_id,
            Match.match_date == target_date,
            Match.status == MatchStatus.COMPLETED,
            Match.stage != MatchStage.TRAINING,
        )
    )

    if venue_id:
        query = query.filter(Match.venue_id == venue_id)

    matches = query.order_by(Match.venue_id, Match.match_order).all()

    reports = []
    for match in matches:
        # 得点情報を整形
        goals = []
        for goal in sorted(match.goals, key=lambda g: (g.half, g.minute)):
            half_text = "前半" if goal.half == 1 else "後半"
            display = f"{half_text}{goal.minute}分 {goal.team.name} {goal.player_name}"
            if goal.is_own_goal:
                display += "(OG)"
            if goal.is_penalty:
                display += "(PK)"

            goals.append(GoalReport(
                minute=goal.minute,
                half=goal.half,
                team_name=goal.team.name,
                player_name=goal.player_name,
                display_text=display,
            ))

        # スコア文字列を生成
        h1 = match.home_score_half1 or 0
        h2 = match.home_score_half2 or 0
        a1 = match.away_score_half1 or 0
        a2 = match.away_score_half2 or 0

        score_pk = None
        if match.has_penalty_shootout:
            score_pk = f"{match.home_pk}-{match.away_pk}"

        reports.append(MatchReport(
            match_number=match.match_order,
            kickoff_time=match.match_time.strftime("%H:%M"),
            home_team_name=match.home_team.short_name or match.home_team.name,
            away_team_name=match.away_team.short_name or match.away_team.name,
            score_half1=f"{h1}-{a1}",
            score_half2=f"{h2}-{a2}",
            score_total=f"{h1 + h2}-{a1 + a2}",
            score_pk=score_pk,
            goals=goals,
        ))

    return reports


# ================== PDF/Excel出力 ==================
# 要件準拠パス: POST /tournaments/{id}/reports/daily, POST /tournaments/{id}/reports/final

from pydantic import BaseModel

class DailyReportRequest(BaseModel):
    """日別報告書リクエスト"""
    date: date
    venue_ids: Optional[List[int]] = None


@router.post("/tournaments/{tournament_id}/daily")
def generate_daily_report_pdf(
    tournament_id: int,
    request: DailyReportRequest,
    db: Session = Depends(get_db),
):
    """
    日別試合結果報告書をPDFで出力

    要件準拠パス: POST /tournaments/{id}/reports/daily

    Request Body:
        date: 対象日
        venue_ids: 会場IDリスト（省略時は全会場）
    """
    from services.report_service import ReportService

    report_service = ReportService(db)
    venue_id = request.venue_ids[0] if request.venue_ids and len(request.venue_ids) == 1 else None

    try:
        pdf_buffer = report_service.generate_pdf(tournament_id, request.date, venue_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF生成に失敗しました: {str(e)}"
        )

    filename = f"浦和カップ_試合結果_{request.date.isoformat()}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
        }
    )


@router.post("/tournaments/{tournament_id}/final")
def generate_final_report_pdf(
    tournament_id: int,
    db: Session = Depends(get_db),
):
    """
    最終結果報告書をPDFで出力

    要件準拠パス: POST /tournaments/{id}/reports/final
    """
    from services.reports import FinalResultReportGenerator

    try:
        generator = FinalResultReportGenerator(
            db=db,
            tournament_id=tournament_id,
        )
        pdf_buffer = generator.generate()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"最終結果報告書の生成に失敗しました: {str(e)}"
        )

    filename = f"浦和カップ_最終結果.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
        }
    )


# レガシーAPI（後方互換性のため維持）
@router.get("/export/pdf", include_in_schema=False)
def export_report_pdf(
    tournament_id: int = Query(..., description="大会ID"),
    target_date: date = Query(..., description="対象日"),
    venue_id: Optional[int] = Query(None, description="会場ID"),
    db: Session = Depends(get_db),
):
    """
    報告書をPDFで出力（レガシー）

    指定日・指定会場の試合結果をPDF形式で出力
    """
    from services.report_service import ReportService

    report_service = ReportService(db)

    try:
        pdf_buffer = report_service.generate_pdf(tournament_id, target_date, venue_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF生成に失敗しました: {str(e)}"
        )

    filename = f"report_{target_date.isoformat()}"
    if venue_id:
        filename += f"_venue{venue_id}"
    filename += ".pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/export/excel")
def export_report_excel(
    tournament_id: int = Query(..., description="大会ID"),
    target_date: date = Query(..., description="対象日"),
    venue_id: Optional[int] = Query(None, description="会場ID"),
    db: Session = Depends(get_db),
):
    """
    報告書をExcelで出力

    指定日・指定会場の試合結果をExcel形式で出力
    """
    from services.report_service import ReportService

    report_service = ReportService(db)

    try:
        excel_buffer = report_service.generate_excel(tournament_id, target_date, venue_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Excel生成に失敗しました: {str(e)}"
        )

    filename = f"report_{target_date.isoformat()}"
    if venue_id:
        filename += f"_venue{venue_id}"
    filename += ".xlsx"

    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/export/final-day-schedule")
def export_final_day_schedule_pdf(
    tournament_id: int = Query(..., description="大会ID"),
    target_date: date = Query(..., description="対象日"),
    db: Session = Depends(get_db),
):
    """
    最終日組み合わせ表をPDFで出力

    予選終了後に生成される最終日の組み合わせ表
    """
    from services.reports import FinalDayScheduleGenerator

    try:
        generator = FinalDayScheduleGenerator(
            db=db,
            tournament_id=tournament_id,
            target_date=target_date,
        )
        pdf_buffer = generator.generate()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"最終日組み合わせ表の生成に失敗しました: {str(e)}"
        )

    filename = f"final_day_schedule_{target_date.isoformat()}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/export/final-result", include_in_schema=False)
def export_final_result_pdf(
    tournament_id: int = Query(..., description="大会ID"),
    db: Session = Depends(get_db),
):
    """
    最終結果報告書をPDFで出力（レガシー）

    決勝トーナメントの結果、最終順位、優秀選手を含む
    新しいAPI: POST /tournaments/{id}/final
    """
    from services.reports import FinalResultReportGenerator

    try:
        generator = FinalResultReportGenerator(
            db=db,
            tournament_id=tournament_id,
        )
        pdf_buffer = generator.generate()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"最終結果報告書の生成に失敗しました: {str(e)}"
        )

    filename = f"final_result_tournament_{tournament_id}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/export/group-standings")
def export_group_standings_pdf(
    tournament_id: int = Query(..., description="大会ID"),
    group_id: Optional[str] = Query(None, description="グループID（省略時は全グループ）"),
    db: Session = Depends(get_db),
):
    """
    グループ順位表をPDFで出力

    予選リーグ終了後のグループ別順位表
    """
    from models.group import Group
    from models.standing import Standing
    from models.team import Team

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    query = db.query(Standing).filter(Standing.tournament_id == tournament_id)
    if group_id:
        query = query.filter(Standing.group_id == group_id)

    standings = query.order_by(Standing.group_id, Standing.rank).all()

    if not standings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="順位データが見つかりません"
        )

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ReportLabがインストールされていません"
        )

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    try:
        pdfmetrics.registerFont(TTFont('Gothic', 'C:/Windows/Fonts/msgothic.ttc'))
        font_name = 'Gothic'
    except Exception:
        try:
            pdfmetrics.registerFont(TTFont('Gothic', '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc'))
            font_name = 'Gothic'
        except Exception:
            font_name = 'Helvetica'

    y = height - 20 * mm

    c.setFont(font_name, 16)
    c.drawString(30 * mm, y, f"{tournament.name} グループ順位表")
    y -= 15 * mm

    current_group = None
    for standing in standings:
        if standing.group_id != current_group:
            if current_group is not None:
                y -= 10 * mm

            if y < 80 * mm:
                c.showPage()
                y = height - 20 * mm
                c.setFont(font_name, 12)

            current_group = standing.group_id
            group = db.query(Group).filter(Group.id == standing.group_id).first()
            group_name = group.name if group else standing.group_id

            c.setFont(font_name, 12)
            c.drawString(30 * mm, y, f"【{group_name}】")
            y -= 8 * mm

            c.setFont(font_name, 9)
            c.drawString(30 * mm, y, "順位")
            c.drawString(45 * mm, y, "チーム名")
            c.drawString(100 * mm, y, "試合")
            c.drawString(115 * mm, y, "勝")
            c.drawString(125 * mm, y, "分")
            c.drawString(135 * mm, y, "負")
            c.drawString(145 * mm, y, "得点")
            c.drawString(160 * mm, y, "失点")
            c.drawString(175 * mm, y, "得失点差")
            y -= 5 * mm

            c.line(30 * mm, y + 2 * mm, 190 * mm, y + 2 * mm)

        team = db.query(Team).filter(Team.id == standing.team_id).first()
        team_name = team.short_name or team.name if team else "Unknown"

        c.setFont(font_name, 9)
        c.drawString(32 * mm, y, str(standing.rank))
        c.drawString(45 * mm, y, team_name[:15])
        c.drawString(102 * mm, y, str(standing.played))
        c.drawString(117 * mm, y, str(standing.won))
        c.drawString(127 * mm, y, str(standing.drawn))
        c.drawString(137 * mm, y, str(standing.lost))
        c.drawString(147 * mm, y, str(standing.goals_for))
        c.drawString(162 * mm, y, str(standing.goals_against))
        c.drawString(177 * mm, y, str(standing.goal_difference))
        y -= 5 * mm

    c.setFont(font_name, 8)
    c.drawString(30 * mm, 15 * mm, "浦和カップ運営事務局")

    c.save()
    buffer.seek(0)

    filename = f"group_standings_tournament_{tournament_id}"
    if group_id:
        filename += f"_group_{group_id}"
    filename += ".pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


# ================== プレビュー機能 ==================

@router.get("/preview/pdf")
def preview_report_pdf(
    tournament_id: int = Query(..., description="大会ID"),
    target_date: date = Query(..., description="対象日"),
    venue_id: Optional[int] = Query(None, description="会場ID"),
    db: Session = Depends(get_db),
):
    """
    報告書PDFのプレビュー（Base64）

    PDFをBase64エンコードして返す。フロントエンドでiframeに表示可能。
    """
    import base64
    from services.report_service import ReportService

    report_service = ReportService(db)

    try:
        pdf_buffer = report_service.generate_pdf(tournament_id, target_date, venue_id)
        pdf_bytes = pdf_buffer.read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDFプレビュー生成に失敗しました: {str(e)}"
        )

    return {
        "content": pdf_base64,
        "content_type": "application/pdf",
        "filename": f"preview_{target_date.isoformat()}.pdf",
    }


@router.get("/preview/final-result")
def preview_final_result_pdf(
    tournament_id: int = Query(..., description="大会ID"),
    db: Session = Depends(get_db),
):
    """
    最終結果報告書PDFのプレビュー（Base64）
    """
    import base64
    from services.reports import FinalResultReportGenerator

    try:
        generator = FinalResultReportGenerator(
            db=db,
            tournament_id=tournament_id,
        )
        pdf_buffer = generator.generate()
        pdf_bytes = pdf_buffer.read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"最終結果PDFプレビュー生成に失敗しました: {str(e)}"
        )

    return {
        "content": pdf_base64,
        "content_type": "application/pdf",
        "filename": f"preview_final_result_{tournament_id}.pdf",
    }


# ================== 未入力警告チェック ==================

@router.get("/check-incomplete")
def check_incomplete_data(
    tournament_id: int = Query(..., description="大会ID"),
    target_date: Optional[date] = Query(None, description="対象日（省略時は最終結果チェック）"),
    db: Session = Depends(get_db),
):
    """
    未入力データをチェック

    報告書出力前に不足しているデータを警告として返す。

    Returns:
        warnings: 未入力項目のリスト
        can_export: 出力可能かどうか（致命的な未入力がなければTrue）
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    warnings = []
    critical_warnings = []

    if target_date:
        # 日別報告書のチェック
        warnings, critical_warnings = _check_daily_report_data(db, tournament_id, target_date)
    else:
        # 最終結果報告書のチェック
        warnings, critical_warnings = _check_final_result_data(db, tournament_id)

    return {
        "warnings": warnings,
        "critical_warnings": critical_warnings,
        "can_export": len(critical_warnings) == 0,
        "warning_count": len(warnings),
        "critical_count": len(critical_warnings),
    }


def _check_daily_report_data(db: Session, tournament_id: int, target_date: date):
    """日別報告書の未入力チェック"""
    warnings = []
    critical_warnings = []

    # 指定日の試合を取得
    matches = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.match_date == target_date,
        Match.stage != MatchStage.TRAINING,
    ).all()

    if not matches:
        critical_warnings.append({
            "type": "no_matches",
            "message": f"{target_date}の試合データがありません",
            "field": "matches",
        })
        return warnings, critical_warnings

    # 各試合のチェック
    for match in matches:
        match_label = f"第{match.match_order}試合"
        if match.venue:
            match_label = f"{match.venue.name} {match_label}"

        # 試合結果が未入力
        if match.status != MatchStatus.COMPLETED:
            critical_warnings.append({
                "type": "incomplete_match",
                "message": f"{match_label}の結果が未入力です",
                "field": "match_result",
                "match_id": match.id,
            })
        else:
            # スコアチェック
            if match.home_score_half1 is None or match.home_score_half2 is None:
                warnings.append({
                    "type": "missing_score",
                    "message": f"{match_label}のホームスコアが不完全です",
                    "field": "home_score",
                    "match_id": match.id,
                })
            if match.away_score_half1 is None or match.away_score_half2 is None:
                warnings.append({
                    "type": "missing_score",
                    "message": f"{match_label}のアウェイスコアが不完全です",
                    "field": "away_score",
                    "match_id": match.id,
                })

            # 得点経過チェック（得点があるのにGoalレコードがない場合）
            total_score = (match.home_score_half1 or 0) + (match.home_score_half2 or 0) + \
                          (match.away_score_half1 or 0) + (match.away_score_half2 or 0)
            goal_count = len(match.goals) if hasattr(match, 'goals') else 0
            if total_score > 0 and goal_count == 0:
                warnings.append({
                    "type": "missing_goals",
                    "message": f"{match_label}の得点経過が未入力です（{total_score}点）",
                    "field": "goals",
                    "match_id": match.id,
                })
            elif total_score != goal_count:
                warnings.append({
                    "type": "goal_mismatch",
                    "message": f"{match_label}の得点経過数（{goal_count}）がスコア合計（{total_score}）と一致しません",
                    "field": "goals",
                    "match_id": match.id,
                })

    return warnings, critical_warnings


def _check_final_result_data(db: Session, tournament_id: int):
    """最終結果報告書の未入力チェック"""
    from models.award import Award
    from models.standing import Standing

    warnings = []
    critical_warnings = []

    # 決勝トーナメント試合のチェック
    knockout_matches = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.stage.in_([MatchStage.SEMIFINAL, MatchStage.THIRD_PLACE, MatchStage.FINAL]),
    ).all()

    stage_names = {
        MatchStage.SEMIFINAL: "準決勝",
        MatchStage.THIRD_PLACE: "3位決定戦",
        MatchStage.FINAL: "決勝",
    }

    for match in knockout_matches:
        stage_name = stage_names.get(match.stage, str(match.stage))
        if match.status != MatchStatus.COMPLETED:
            critical_warnings.append({
                "type": "incomplete_knockout",
                "message": f"{stage_name}の結果が未入力です",
                "field": "knockout_result",
                "match_id": match.id,
            })

    # 優秀選手のチェック
    awards = db.query(Award).filter(Award.tournament_id == tournament_id).all()
    mvp_count = sum(1 for a in awards if a.award_type == 'mvp')
    outstanding_count = sum(1 for a in awards if a.award_type == 'outstanding')

    if mvp_count == 0:
        warnings.append({
            "type": "missing_mvp",
            "message": "最優秀選手（MVP）が未登録です",
            "field": "awards",
        })
    if outstanding_count < 3:
        warnings.append({
            "type": "missing_outstanding",
            "message": f"優秀選手が{outstanding_count}名のみです（推奨: 3名以上）",
            "field": "awards",
        })

    # 最終順位のチェック（1位〜4位）
    first_places = db.query(Standing).filter(
        Standing.tournament_id == tournament_id,
        Standing.rank == 1,
    ).count()
    if first_places < 4:
        warnings.append({
            "type": "missing_standings",
            "message": f"グループ1位が{first_places}チームのみです（4チーム必要）",
            "field": "standings",
        })

    return warnings, critical_warnings


@router.get("/summary/{tournament_id}")
def get_tournament_summary(
    tournament_id: int,
    db: Session = Depends(get_db),
):
    """
    大会サマリーを取得

    ダッシュボード用の統計情報
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    from models.team import Team
    from models.match import Match

    # チーム数
    team_count = db.query(Team).filter(Team.tournament_id == tournament_id).count()

    # 試合数
    match_stats = db.query(Match).filter(Match.tournament_id == tournament_id)
    total_matches = match_stats.count()
    completed_matches = match_stats.filter(Match.status == MatchStatus.COMPLETED).count()

    # ステージ別試合数
    stage_counts = {}
    for stage in MatchStage:
        count = match_stats.filter(Match.stage == stage).count()
        if count > 0:
            stage_counts[stage.value] = count

    # 総得点
    total_goals = db.query(Goal).join(Match).filter(
        Match.tournament_id == tournament_id
    ).count()

    return {
        "tournament_id": tournament_id,
        "tournament_name": tournament.name,
        "team_count": team_count,
        "total_matches": total_matches,
        "completed_matches": completed_matches,
        "completion_rate": round(completed_matches / total_matches * 100, 1) if total_matches > 0 else 0,
        "stage_counts": stage_counts,
        "total_goals": total_goals,
    }
