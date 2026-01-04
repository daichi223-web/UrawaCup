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

@router.get("/sender-settings/{tournament_id}")
def get_sender_settings(
    tournament_id: int,
    db: Session = Depends(get_db),
):
    """報告書発信元設定を取得"""
    from schemas.report import SenderSettingsResponse

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


@router.patch("/sender-settings/{tournament_id}", response_model=SenderSettingsResponse)
def update_sender_settings(
    tournament_id: int,
    settings: SenderSettingsUpdate,
    db: Session = Depends(get_db),
):
    """報告書発信元設定を更新"""

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

@router.get("/export/pdf")
def export_report_pdf(
    tournament_id: int = Query(..., description="大会ID"),
    target_date: date = Query(..., description="対象日"),
    venue_id: Optional[int] = Query(None, description="会場ID"),
    db: Session = Depends(get_db),
):
    """
    報告書をPDFで出力

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


@router.get("/export/final-result")
def export_final_result_pdf(
    tournament_id: int = Query(..., description="大会ID"),
    db: Session = Depends(get_db),
):
    """
    最終結果報告書をPDFで出力

    決勝トーナメントの結果、最終順位、優秀選手を含む
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
