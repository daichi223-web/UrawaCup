"""
Match（試合）ルーター
試合のCRUD操作、日程生成、スコア入力を提供
"""

from datetime import datetime, date, time, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.match import Match, MatchStage, MatchStatus, MatchResult
from models.tournament import Tournament
from models.team import Team
from models.venue import Venue
from models.goal import Goal
from models.group import Group
from models.exclusion_pair import ExclusionPair
from schemas.match import (
    MatchCreate,
    MatchUpdate,
    MatchResponse,
    MatchWithDetails,
    MatchList,
    MatchScoreInput,
    MatchLock,
    MatchApproveRequest,
    MatchRejectRequest,
    MatchApprovalResponse,
    PendingMatchesResponse,
    ApprovalStatus,
    SwapTeamsRequest,
    SwapTeamsResponse,
)
from schemas.goal import GoalInput
from models.match import ApprovalStatus as ModelApprovalStatus
from models.user import User
from utils.auth import (
    get_current_user,
    get_current_user_optional,
    require_admin,
    require_venue_manager,
    check_match_permission,
)

router = APIRouter()


@router.get("/", response_model=MatchList)
def get_matches(
    tournament_id: Optional[int] = Query(None, description="大会IDでフィルタ"),
    group_id: Optional[str] = Query(None, pattern="^[A-D]$", description="グループでフィルタ"),
    venue_id: Optional[int] = Query(None, description="会場でフィルタ"),
    match_date: Optional[date] = Query(None, description="試合日でフィルタ"),
    stage: Optional[MatchStage] = Query(None, description="ステージでフィルタ"),
    status_filter: Optional[MatchStatus] = Query(None, alias="status", description="ステータスでフィルタ"),
    approval_status: Optional[ApprovalStatus] = Query(None, description="承認ステータスでフィルタ"),
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    db: Session = Depends(get_db),
):
    """試合一覧を取得"""
    query = (
        db.query(Match)
        .options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            joinedload(Match.venue),
            joinedload(Match.group),
        )
    )

    if tournament_id:
        query = query.filter(Match.tournament_id == tournament_id)
    if group_id:
        query = query.filter(Match.group_id == group_id)
    if venue_id:
        query = query.filter(Match.venue_id == venue_id)
    if match_date:
        query = query.filter(Match.match_date == match_date)
    if stage:
        query = query.filter(Match.stage == stage)
    if status_filter:
        query = query.filter(Match.status == status_filter)
    if approval_status:
        query = query.filter(Match.approval_status == ModelApprovalStatus(approval_status.value))

    total = query.count()
    matches = (
        query.order_by(Match.match_date, Match.venue_id, Match.match_order)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return MatchList(matches=matches, total=total)


@router.get("/{match_id}", response_model=MatchWithDetails)
def get_match(
    match_id: int,
    db: Session = Depends(get_db),
):
    """試合詳細を取得（チーム情報、得点情報含む）"""
    match = (
        db.query(Match)
        .options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            joinedload(Match.venue),
            joinedload(Match.group),
            joinedload(Match.goals),
        )
        .filter(Match.id == match_id)
        .first()
    )
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"試合が見つかりません (ID: {match_id})"
        )
    return match


@router.post("/", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
def create_match(
    match_data: MatchCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """新規試合を作成（管理者専用）"""
    # 大会・会場・チームの存在確認
    tournament = db.query(Tournament).filter(Tournament.id == match_data.tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {match_data.tournament_id})"
        )

    venue = db.query(Venue).filter(Venue.id == match_data.venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会場が見つかりません (ID: {match_data.venue_id})"
        )

    home_team = db.query(Team).filter(Team.id == match_data.home_team_id).first()
    away_team = db.query(Team).filter(Team.id == match_data.away_team_id).first()
    if not home_team or not away_team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたチームが見つかりません"
        )

    # 同一チーム同士の対戦は不可
    if match_data.home_team_id == match_data.away_team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="同一チーム同士の対戦は登録できません"
        )

    match = Match(**match_data.model_dump(by_alias=False))
    db.add(match)
    db.commit()
    db.refresh(match)

    return match


@router.put("/{match_id}", response_model=MatchResponse)
def update_match(
    match_id: int,
    match_data: MatchUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """試合情報を更新（管理者専用）"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"試合が見つかりません (ID: {match_id})"
        )

    if match.is_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="この試合は現在編集中です"
        )

    update_data = match_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(match, field, value)

    db.commit()
    db.refresh(match)

    return match


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_match(
    match_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """試合を削除（管理者専用）"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"試合が見つかりません (ID: {match_id})"
        )

    db.delete(match)
    db.commit()

    return None


@router.put("/{match_id}/score", response_model=MatchWithDetails)
async def input_match_score(
    match_id: int,
    score_data: MatchScoreInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_venue_manager),
):
    """
    試合結果を入力（会場担当者以上）

    スコアと得点者情報を入力し、試合を完了状態にする。
    順位表は自動的に更新される。
    会場担当者は自分の担当会場の試合のみ入力可能。
    """
    match = (
        db.query(Match)
        .options(joinedload(Match.goals))
        .filter(Match.id == match_id)
        .first()
    )
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"試合が見つかりません (ID: {match_id})"
        )

    # 会場担当者の権限チェック
    check_match_permission(current_user, match)

    if match.is_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="この試合は現在編集中です"
        )

    # スコアを設定
    match.home_score_half1 = score_data.home_score_half1
    match.home_score_half2 = score_data.home_score_half2
    match.away_score_half1 = score_data.away_score_half1
    match.away_score_half2 = score_data.away_score_half2
    match.has_penalty_shootout = score_data.has_penalty_shootout
    match.home_pk = score_data.home_pk
    match.away_pk = score_data.away_pk

    # 合計得点を計算
    match.calculate_total_scores()

    # 試合結果を判定
    match.determine_result()

    # ステータスを完了に、承認待ちに設定
    match.status = MatchStatus.COMPLETED
    match.entered_at = datetime.utcnow()
    match.entered_by = current_user.id
    match.approval_status = ModelApprovalStatus.PENDING  # 承認待ちに設定

    # 既存の得点情報を削除
    db.query(Goal).filter(Goal.match_id == match_id).delete()

    # 得点情報を登録
    for goal_data in score_data.goals:
        goal = Goal(
            match_id=match_id,
            team_id=goal_data.team_id,
            player_id=goal_data.player_id,
            player_name=goal_data.player_name,
            minute=goal_data.minute,
            half=goal_data.half,
            is_own_goal=goal_data.is_own_goal,
            is_penalty=goal_data.is_penalty,
            notes=goal_data.notes,
        )
        db.add(goal)

    db.commit()

    # 順位表を更新（予選リーグの場合）
    if match.stage == MatchStage.PRELIMINARY and match.group_id:
        from services.standing_service import StandingService
        standing_service = StandingService(db)
        standing_service.update_group_standings(match.tournament_id, match.group_id)

    db.refresh(match)

    # 詳細情報を取得して返す
    match = (
        db.query(Match)
        .options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            joinedload(Match.venue),
            joinedload(Match.group),
            joinedload(Match.goals),
        )
        .filter(Match.id == match_id)
        .first()
    )

    # WebSocketで更新通知を送信
    from utils.websocket import manager
    await manager.send_match_update(
        match_id=match.id,
        tournament_id=match.tournament_id,
        action="score_updated",
        details={
            "home_score": match.home_score_total,
            "away_score": match.away_score_total,
            "group_id": match.group_id,
            "status": match.status.value,
        }
    )

    # 順位表更新通知も送信（予選リーグの場合）
    if match.stage == MatchStage.PRELIMINARY and match.group_id:
        await manager.send_standing_update(
            tournament_id=match.tournament_id,
            group_id=match.group_id,
            details={"reason": "match_result_updated"}
        )

    return match


@router.post("/{match_id}/lock", response_model=MatchLock)
def lock_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_venue_manager),
):
    """試合の編集ロックを取得（会場担当者以上）"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"試合が見つかりません (ID: {match_id})"
        )

    # 会場担当者の権限チェック
    check_match_permission(current_user, match)

    if match.is_locked and match.locked_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="この試合は他のユーザーが編集中です"
        )

    match.is_locked = True
    match.locked_by = current_user.id
    match.locked_at = datetime.utcnow()

    db.commit()
    db.refresh(match)

    return MatchLock(
        match_id=match.id,
        is_locked=match.is_locked,
        locked_by=match.locked_by,
        locked_at=match.locked_at,
    )


@router.post("/{match_id}/unlock", response_model=MatchLock)
def unlock_match(
    match_id: int,
    force: bool = Query(False, description="強制解除（管理者のみ）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_venue_manager),
):
    """試合の編集ロックを解除（会場担当者以上）"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"試合が見つかりません (ID: {match_id})"
        )

    # 会場担当者の権限チェック
    check_match_permission(current_user, match)

    # 強制解除は管理者のみ
    from models.user import UserRole
    if match.is_locked and match.locked_by != current_user.id:
        if not force:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="他のユーザーがロックしています。強制解除するにはforce=trueを指定してください"
            )
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="強制解除は管理者のみ可能です"
            )

    match.is_locked = False
    match.locked_by = None
    match.locked_at = None

    db.commit()
    db.refresh(match)

    return MatchLock(
        match_id=match.id,
        is_locked=match.is_locked,
    )


# =============================================================================
# 承認フロー関連エンドポイント
# =============================================================================

@router.get("/pending", response_model=PendingMatchesResponse)
def get_pending_matches(
    tournament_id: Optional[int] = Query(None, description="大会IDでフィルタ"),
    venue_id: Optional[int] = Query(None, description="会場でフィルタ"),
    db: Session = Depends(get_db),
):
    """
    承認待ちの試合一覧を取得

    会場担当者が結果入力後、本部承認待ちの試合を一覧表示。
    管理者はこの一覧から承認/却下を行う。
    """
    query = (
        db.query(Match)
        .options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            joinedload(Match.venue),
            joinedload(Match.group),
            joinedload(Match.goals),
            joinedload(Match.entered_by_user),
        )
        .filter(Match.approval_status == ModelApprovalStatus.PENDING)
    )

    if tournament_id:
        query = query.filter(Match.tournament_id == tournament_id)
    if venue_id:
        query = query.filter(Match.venue_id == venue_id)

    matches = query.order_by(Match.match_date, Match.venue_id, Match.match_order).all()

    return PendingMatchesResponse(matches=matches, total=len(matches))


@router.post("/{match_id}/approve", response_model=MatchApprovalResponse)
async def approve_match(
    match_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    試合結果を承認（管理者専用）

    会場担当者が入力した試合結果を管理者が確認し承認する。
    承認後、順位表が更新される。
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"試合が見つかりません (ID: {match_id})"
        )

    # 承認待ち状態かチェック
    if match.approval_status != ModelApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"この試合は承認待ち状態ではありません (現在: {match.approval_status})"
        )

    # 承認処理
    match.approval_status = ModelApprovalStatus.APPROVED
    match.approved_by = admin.id
    match.approved_at = datetime.utcnow()
    match.rejection_reason = None

    db.commit()

    # 順位表を更新（予選リーグの場合）
    if match.stage == MatchStage.PRELIMINARY and match.group_id:
        from services.standing_service import StandingService
        standing_service = StandingService(db)
        standing_service.update_group_standings(match.tournament_id, match.group_id)

    db.refresh(match)

    # WebSocketで更新通知を送信
    from utils.websocket import manager
    await manager.send_match_update(
        match_id=match.id,
        tournament_id=match.tournament_id,
        action="approved",
        details={
            "approved_by": admin.display_name,
            "group_id": match.group_id,
        }
    )

    # 承認状態更新通知
    await manager.send_approval_update(
        match_id=match.id,
        tournament_id=match.tournament_id,
        status="approved",
        details={"approved_by_name": admin.display_name}
    )

    # 順位表更新通知も送信（予選リーグの場合）
    if match.stage == MatchStage.PRELIMINARY and match.group_id:
        await manager.send_standing_update(
            tournament_id=match.tournament_id,
            group_id=match.group_id,
            details={"reason": "match_approved"}
        )

    return MatchApprovalResponse(
        match_id=match.id,
        approval_status=ApprovalStatus(match.approval_status.value),
        approved_by=match.approved_by,
        approved_by_name=admin.display_name,
        approved_at=match.approved_at,
        rejection_reason=None,
        message="試合結果を承認しました"
    )


@router.post("/{match_id}/reject", response_model=MatchApprovalResponse)
def reject_match(
    match_id: int,
    request: MatchRejectRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    試合結果を却下（管理者専用）

    会場担当者が入力した試合結果に問題がある場合に却下する。
    却下理由を必須とし、会場担当者に再入力を促す。
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"試合が見つかりません (ID: {match_id})"
        )

    # 承認待ち状態かチェック
    if match.approval_status != ModelApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"この試合は承認待ち状態ではありません (現在: {match.approval_status})"
        )

    # 却下処理
    match.approval_status = ModelApprovalStatus.REJECTED
    match.approved_by = admin.id
    match.approved_at = datetime.utcnow()
    match.rejection_reason = request.reason
    # ステータスを予定に戻し、再入力を可能にする
    match.status = MatchStatus.SCHEDULED

    db.commit()
    db.refresh(match)

    return MatchApprovalResponse(
        match_id=match.id,
        approval_status=ApprovalStatus(match.approval_status.value),
        approved_by=match.approved_by,
        approved_by_name=admin.display_name,
        approved_at=match.approved_at,
        rejection_reason=match.rejection_reason,
        message=f"試合結果を却下しました: {request.reason}"
    )


@router.post("/{match_id}/resubmit", response_model=MatchApprovalResponse)
def resubmit_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_venue_manager),
):
    """
    却下された試合結果を再提出（会場担当者以上）

    却下された試合結果を修正後、再度承認待ちに変更する。
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"試合が見つかりません (ID: {match_id})"
        )

    # 会場担当者の権限チェック
    check_match_permission(current_user, match)

    # 却下された状態かチェック
    if match.approval_status != ModelApprovalStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"この試合は却下状態ではありません (現在: {match.approval_status})"
        )

    # 再提出処理
    match.approval_status = ModelApprovalStatus.PENDING
    match.approved_by = None
    match.approved_at = None
    match.rejection_reason = None
    match.entered_by = current_user.id
    match.entered_at = datetime.utcnow()

    db.commit()
    db.refresh(match)

    return MatchApprovalResponse(
        match_id=match.id,
        approval_status=ApprovalStatus(match.approval_status.value),
        approved_by=None,
        approved_by_name=None,
        approved_at=None,
        rejection_reason=None,
        message="試合結果を再提出しました"
    )


@router.post("/generate-schedule/{tournament_id}", response_model=MatchList)
def generate_preliminary_schedule(
    tournament_id: int,
    start_time: time = Query(time(9, 30), description="開始時刻"),
    interval_minutes: Optional[int] = Query(None, description="試合間隔（分）、省略時は大会設定を使用"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    予選リーグの日程を自動生成（管理者専用）

    対戦除外設定に基づき、各グループ12試合を生成。
    Day1に6試合、Day2に6試合ずつ配分。
    """
    # 大会の存在確認
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    # 既存の予選試合があるかチェック
    existing = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.stage == MatchStage.PRELIMINARY,
    ).count()
    if existing > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="既に予選リーグの日程が作成されています。再生成する場合は既存の試合を削除してください。"
        )

    # 試合間隔
    match_interval = interval_minutes or tournament.interval_minutes
    match_duration = tournament.match_duration + match_interval

    # 各グループの試合を生成
    created_matches = []

    for group_id in ["A", "B", "C", "D"]:
        # グループのチームを取得
        teams = (
            db.query(Team)
            .filter(
                Team.tournament_id == tournament_id,
                Team.group_id == group_id,
            )
            .order_by(Team.group_order)
            .all()
        )

        if len(teams) != 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"グループ{group_id}のチーム数が6チームではありません（現在: {len(teams)}チーム）"
            )

        # 会場を取得
        venue = db.query(Venue).filter(
            Venue.tournament_id == tournament_id,
            Venue.group_id == group_id,
        ).first()
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"グループ{group_id}に会場が設定されていません"
            )

        # 除外ペアを取得
        exclusion_pairs = db.query(ExclusionPair).filter(
            ExclusionPair.tournament_id == tournament_id,
            ExclusionPair.group_id == group_id,
        ).all()

        excluded_set = set()
        for pair in exclusion_pairs:
            excluded_set.add((pair.team1_id, pair.team2_id))
            excluded_set.add((pair.team2_id, pair.team1_id))

        # 総当たりから除外ペアを除いた対戦カードを生成
        matchups = []
        for i, team1 in enumerate(teams):
            for team2 in teams[i + 1:]:
                if (team1.id, team2.id) not in excluded_set:
                    matchups.append((team1.id, team2.id))

        if len(matchups) != 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"グループ{group_id}の対戦数が12試合になりません（現在: {len(matchups)}試合）。除外設定を確認してください。"
            )

        # Day1, Day2に振り分け
        day1_date = tournament.start_date
        day2_date = tournament.start_date + timedelta(days=1)

        for idx, (home_id, away_id) in enumerate(matchups):
            is_day1 = idx < 6
            match_date = day1_date if is_day1 else day2_date
            match_order = (idx % 6) + 1

            # 開始時刻を計算
            minutes_offset = (match_order - 1) * match_duration
            match_time = (
                datetime.combine(date.today(), start_time) +
                timedelta(minutes=minutes_offset)
            ).time()

            match = Match(
                tournament_id=tournament_id,
                group_id=group_id,
                venue_id=venue.id,
                home_team_id=home_id,
                away_team_id=away_id,
                match_date=match_date,
                match_time=match_time,
                match_order=match_order,
                stage=MatchStage.PRELIMINARY,
                status=MatchStatus.SCHEDULED,
            )
            db.add(match)
            created_matches.append(match)

    db.commit()

    for match in created_matches:
        db.refresh(match)

    return MatchList(matches=created_matches, total=len(created_matches))


@router.get("/today/{tournament_id}", response_model=MatchList)
def get_today_matches(
    tournament_id: int,
    target_date: Optional[date] = Query(None, description="対象日（省略時は本日）"),
    db: Session = Depends(get_db),
):
    """本日（または指定日）の試合一覧を取得"""
    query_date = target_date or date.today()

    matches = (
        db.query(Match)
        .filter(
            Match.tournament_id == tournament_id,
            Match.match_date == query_date,
        )
        .order_by(Match.venue_id, Match.match_order)
        .all()
    )

    return MatchList(matches=matches, total=len(matches))


@router.post("/generate-training/{tournament_id}", response_model=MatchList)
def generate_training_matches(
    tournament_id: int,
    match_date: date = Query(..., description="試合日（通常Day3）"),
    start_time: time = Query(time(9, 0), description="開始時刻"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    研修試合（順位リーグ）の組み合わせを自動生成（管理者専用）

    【順位リーグ方式】
    1. 全体順位を計算（グループ内順位→勝点→得失点差→総得点→ランダム）
    2. 各グループ1位を除いた残りチームを4つの順位リーグに振り分け
    3. 各リーグ内で総当たり戦を生成
    """
    from services.standing_service import StandingService

    # 大会の存在確認
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    # 順位リーグ用の会場を取得（決勝会場以外で最終日用）
    training_venues = db.query(Venue).filter(
        Venue.tournament_id == tournament_id,
        Venue.for_final_day == True,
        Venue.is_finals_venue == False,
    ).order_by(Venue.id).all()

    if len(training_venues) < 4:
        all_venues = db.query(Venue).filter(Venue.tournament_id == tournament_id).all()
        venue_info = [f"{v.name}(for_final_day={v.for_final_day}, is_finals_venue={v.is_finals_venue})" for v in all_venues]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"順位リーグ用の会場が不足しています。必要: 4会場, 現在: {len(training_venues)}会場。"
                   f"設定画面で会場の「最終日の順位リーグ会場として使用」にチェックを入れてください。"
                   f"（決勝会場は除外されます）現在の会場: {venue_info}"
        )

    # 予選リーグの対戦履歴を取得（再戦チェック用）
    preliminary_matches = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.stage == MatchStage.PRELIMINARY,
    ).all()

    played_pairs = set()
    for m in preliminary_matches:
        pair = tuple(sorted([m.home_team_id, m.away_team_id]))
        played_pairs.add(pair)

    # StandingServiceを使用して順位リーグ振り分けを取得
    standing_service = StandingService(db)
    knockout_teams, position_leagues, warnings = standing_service.get_position_league_teams(tournament_id)

    created_matches = []
    match_interval = tournament.match_duration + tournament.interval_minutes
    rematch_warnings = []

    # 総当たり対戦順序の定義
    def get_round_robin_pairs(team_count: int) -> list:
        """チーム数に応じた総当たり対戦順序を返す"""
        if team_count == 5:
            return [(0, 1), (2, 3), (0, 4), (1, 2), (3, 4),
                    (0, 2), (1, 3), (2, 4), (0, 3), (1, 4)]
        elif team_count == 4:
            return [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]
        elif team_count == 3:
            return [(0, 1), (0, 2), (1, 2)]
        elif team_count == 2:
            return [(0, 1)]
        else:
            # 一般的な総当たり
            pairs = []
            for i in range(team_count):
                for j in range(i + 1, team_count):
                    pairs.append((i, j))
            return pairs

    # 各順位リーグで総当たり戦を生成
    for league_idx, league_teams in enumerate(position_leagues):
        if not league_teams:
            continue

        venue = training_venues[league_idx] if league_idx < len(training_venues) else training_venues[-1]
        team_count = len(league_teams)
        pairs = get_round_robin_pairs(team_count)

        # 順位リーグの順位範囲を計算（表示用）
        first_rank = getattr(league_teams[0], 'overall_rank', league_idx * 5 + 5) if league_teams else 0
        last_rank = getattr(league_teams[-1], 'overall_rank', first_rank + team_count - 1) if league_teams else 0
        rank_range = f"{first_rank}〜{last_rank}位"

        for match_order, (i, j) in enumerate(pairs, 1):
            if i >= len(league_teams) or j >= len(league_teams):
                continue

            team1 = league_teams[i]
            team2 = league_teams[j]

            # 再戦チェック
            pair_key = tuple(sorted([team1.team_id, team2.team_id]))
            is_rematch = pair_key in played_pairs

            if is_rematch:
                rematch_warnings.append({
                    'type': 'rematch',
                    'league': league_idx + 1,
                    'teams': [
                        team1.team.name if team1.team else f"Team#{team1.team_id}",
                        team2.team.name if team2.team else f"Team#{team2.team_id}",
                    ],
                })

            match_time = (
                datetime.combine(date.today(), start_time) +
                timedelta(minutes=(match_order - 1) * match_interval)
            ).time()

            match = Match(
                tournament_id=tournament_id,
                group_id=None,
                venue_id=venue.id,
                home_team_id=team1.team_id,
                away_team_id=team2.team_id,
                match_date=match_date,
                match_time=match_time,
                match_order=match_order,
                stage=MatchStage.TRAINING,
                status=MatchStatus.SCHEDULED,
                notes=f"順位リーグ{league_idx + 1}（{rank_range}）" + (" ⚠️再戦" if is_rematch else ""),
            )
            db.add(match)
            created_matches.append(match)

    db.commit()

    for match in created_matches:
        db.refresh(match)

    # 警告がある場合はログ出力（将来的にはレスポンスに含める）
    all_warnings = warnings + rematch_warnings
    if all_warnings:
        import logging
        logger = logging.getLogger(__name__)
        for w in all_warnings:
            logger.warning(f"順位リーグ生成警告: {w}")

    return MatchList(matches=created_matches, total=len(created_matches))


@router.post("/generate-finals/{tournament_id}", response_model=MatchList)
def generate_final_matches(
    tournament_id: int,
    match_date: date = Query(..., description="試合日（通常Day3）"),
    start_time: time = Query(time(9, 0), description="開始時刻"),
    venue_id: Optional[int] = Query(None, description="決勝会場ID（省略時は駒場スタジアムを自動選択）"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    決勝トーナメントの組み合わせを自動生成（管理者専用）

    各グループ1位の4チームで準決勝・3位決定戦・決勝を生成。
    組み合わせパターン: A1位 vs B1位, C1位 vs D1位
    """
    # 大会の存在確認
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    # 既存の決勝トーナメント試合があるかチェック
    existing_finals = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.stage.in_([MatchStage.SEMIFINAL, MatchStage.THIRD_PLACE, MatchStage.FINAL]),
    ).count()
    if existing_finals > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="既に決勝トーナメントの日程が作成されています。再生成する場合は既存の試合を削除してください。"
        )

    # 決勝会場を取得
    if venue_id:
        final_venue = db.query(Venue).filter(Venue.id == venue_id).first()
        if not final_venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"会場が見つかりません (ID: {venue_id})"
            )
    else:
        # 決勝会場フラグが設定された会場を探す
        final_venue = db.query(Venue).filter(
            Venue.tournament_id == tournament_id,
            Venue.is_finals_venue == True,
        ).first()
        if not final_venue:
            # 代替として for_final_day=True かつ group_id=None の会場を探す
            final_venue = db.query(Venue).filter(
                Venue.tournament_id == tournament_id,
                Venue.for_final_day == True,
                Venue.group_id == None,
            ).first()
        if not final_venue:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="決勝会場が設定されていません。会場設定で「決勝会場フラグ」をオンにしてください。"
            )

    # 各グループ1位を取得
    from services.standing_service import StandingService
    standing_service = StandingService(db)

    qualified_teams = {}
    for group_id in ["A", "B", "C", "D"]:
        standing = standing_service.get_group_first_place(tournament_id, group_id)
        if not standing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"グループ{group_id}の1位がまだ確定していません。予選リーグを完了してください。"
            )
        qualified_teams[group_id] = standing.team_id

    # 試合間隔の計算
    match_interval = tournament.match_duration + tournament.interval_minutes

    # 決勝トーナメントの試合を作成
    # 準決勝1: A1位 vs C1位（対角グループ対戦）
    # 準決勝2: B1位 vs D1位（対角グループ対戦）
    # 3位決定戦: 準決勝敗者同士（後で手動設定またはスコア入力後に更新）
    # 決勝: 準決勝勝者同士（後で手動設定またはスコア入力後に更新）
    created_matches = []

    # 準決勝1 (第1試合): A1位 vs C1位
    sf1_time = start_time
    semifinal1 = Match(
        tournament_id=tournament_id,
        group_id=None,
        venue_id=final_venue.id,
        home_team_id=qualified_teams["A"],
        away_team_id=qualified_teams["C"],
        match_date=match_date,
        match_time=sf1_time,
        match_order=1,
        stage=MatchStage.SEMIFINAL,
        status=MatchStatus.SCHEDULED,
        home_seed="A1位",
        away_seed="C1位",
        notes="準決勝1: A組1位 vs C組1位",
    )
    db.add(semifinal1)
    created_matches.append(semifinal1)

    # 準決勝2 (第2試合): B1位 vs D1位
    sf2_time = (
        datetime.combine(date.today(), start_time) +
        timedelta(minutes=match_interval)
    ).time()
    semifinal2 = Match(
        tournament_id=tournament_id,
        group_id=None,
        venue_id=final_venue.id,
        home_team_id=qualified_teams["B"],
        away_team_id=qualified_teams["D"],
        match_date=match_date,
        match_time=sf2_time,
        match_order=2,
        stage=MatchStage.SEMIFINAL,
        status=MatchStatus.SCHEDULED,
        home_seed="B1位",
        away_seed="D1位",
        notes="準決勝2: B組1位 vs D組1位",
    )
    db.add(semifinal2)
    created_matches.append(semifinal2)

    # 3位決定戦 (第3試合) - チームは準決勝後に決まるのでプレースホルダーとして作成
    # ※初期値として準決勝1のホーム(A) vs 準決勝2のホーム(B)を設定（後で変更可能）
    third_time = (
        datetime.combine(date.today(), start_time) +
        timedelta(minutes=match_interval * 2)
    ).time()
    third_place = Match(
        tournament_id=tournament_id,
        group_id=None,
        venue_id=final_venue.id,
        home_team_id=qualified_teams["A"],  # プレースホルダー（準決勝1敗者）
        away_team_id=qualified_teams["B"],  # プレースホルダー（準決勝2敗者）
        match_date=match_date,
        match_time=third_time,
        match_order=3,
        stage=MatchStage.THIRD_PLACE,
        status=MatchStatus.SCHEDULED,
        notes="3位決定戦（準決勝結果後に組み合わせ確定）",
    )
    db.add(third_place)
    created_matches.append(third_place)

    # 決勝 (第4試合) - チームは準決勝後に決まるのでプレースホルダーとして作成
    # ※初期値として準決勝1のアウェイ(C) vs 準決勝2のアウェイ(D)を設定（後で変更可能）
    final_time = (
        datetime.combine(date.today(), start_time) +
        timedelta(minutes=match_interval * 3)
    ).time()
    final_match = Match(
        tournament_id=tournament_id,
        group_id=None,
        venue_id=final_venue.id,
        home_team_id=qualified_teams["C"],  # プレースホルダー（準決勝1勝者）
        away_team_id=qualified_teams["D"],  # プレースホルダー（準決勝2勝者）
        match_date=match_date,
        match_time=final_time,
        match_order=4,
        stage=MatchStage.FINAL,
        status=MatchStatus.SCHEDULED,
        notes="決勝（準決勝結果後に組み合わせ確定）",
    )
    db.add(final_match)
    created_matches.append(final_match)

    db.commit()

    for match in created_matches:
        db.refresh(match)

    return MatchList(matches=created_matches, total=len(created_matches))


@router.put("/update-finals-bracket/{tournament_id}")
def update_finals_bracket(
    tournament_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    準決勝の結果に基づいて3位決定戦・決勝の組み合わせを更新（管理者専用）

    準決勝が両方完了している場合に呼び出し、
    勝者を決勝へ、敗者を3位決定戦へ振り分ける。
    """
    # 大会の存在確認
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"大会が見つかりません (ID: {tournament_id})"
        )

    # 準決勝を取得
    semifinals = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.stage == MatchStage.SEMIFINAL,
    ).order_by(Match.match_order).all()

    if len(semifinals) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="準決勝が2試合登録されていません"
        )

    # 両方の準決勝が完了しているか確認
    for sf in semifinals:
        if sf.status != MatchStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"準決勝{sf.match_order}がまだ完了していません"
            )
        if sf.result is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"準決勝{sf.match_order}の結果が未確定です"
            )

    # 勝者・敗者を取得
    sf1 = semifinals[0]
    sf2 = semifinals[1]

    if sf1.result == MatchResult.HOME_WIN:
        sf1_winner = sf1.home_team_id
        sf1_loser = sf1.away_team_id
    elif sf1.result == MatchResult.AWAY_WIN:
        sf1_winner = sf1.away_team_id
        sf1_loser = sf1.home_team_id
    else:
        # 引き分け（PK戦で決着がついているはず）
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="準決勝1が引き分けのままです。PK戦の結果を入力してください。"
        )

    if sf2.result == MatchResult.HOME_WIN:
        sf2_winner = sf2.home_team_id
        sf2_loser = sf2.away_team_id
    elif sf2.result == MatchResult.AWAY_WIN:
        sf2_winner = sf2.away_team_id
        sf2_loser = sf2.home_team_id
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="準決勝2が引き分けのままです。PK戦の結果を入力してください。"
        )

    # 3位決定戦を更新
    third_place = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.stage == MatchStage.THIRD_PLACE,
    ).first()

    if third_place:
        third_place.home_team_id = sf1_loser
        third_place.away_team_id = sf2_loser
        third_place.notes = "3位決定戦"

    # 決勝を更新
    final_match = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.stage == MatchStage.FINAL,
    ).first()

    if final_match:
        final_match.home_team_id = sf1_winner
        final_match.away_team_id = sf2_winner
        final_match.notes = "決勝"

    db.commit()

    return {
        "message": "決勝トーナメントの組み合わせを更新しました",
        "third_place": {
            "home_team_id": sf1_loser,
            "away_team_id": sf2_loser,
        },
        "final": {
            "home_team_id": sf1_winner,
            "away_team_id": sf2_winner,
        },
    }


@router.put("/finals/{match_id}/teams")
def update_final_match_teams(
    match_id: int,
    home_team_id: int = Query(..., description="ホームチームID"),
    away_team_id: int = Query(..., description="アウェイチームID"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    決勝トーナメントの試合チームを手動で変更（管理者専用）

    準決勝・3位決定戦・決勝の組み合わせを手動で調整する際に使用。
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"試合が見つかりません (ID: {match_id})"
        )

    # 決勝トーナメントの試合かチェック
    if match.stage not in [MatchStage.SEMIFINAL, MatchStage.THIRD_PLACE, MatchStage.FINAL]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="この機能は決勝トーナメントの試合のみに使用できます"
        )

    # ロック中かチェック
    if match.is_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="この試合は現在編集中です"
        )

    # 同一チーム同士は不可
    if home_team_id == away_team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="同一チーム同士の対戦は登録できません"
        )

    # チームの存在確認
    home_team = db.query(Team).filter(Team.id == home_team_id).first()
    away_team = db.query(Team).filter(Team.id == away_team_id).first()
    if not home_team or not away_team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたチームが見つかりません"
        )

    match.home_team_id = home_team_id
    match.away_team_id = away_team_id

    db.commit()
    db.refresh(match)

    return {
        "message": "試合の組み合わせを更新しました",
        "match_id": match.id,
        "home_team_id": match.home_team_id,
        "away_team_id": match.away_team_id,
    }


@router.get("/finals/{tournament_id}", response_model=MatchList)
def get_final_matches(
    tournament_id: int,
    db: Session = Depends(get_db),
):
    """
    決勝トーナメントの試合一覧を取得

    準決勝・3位決定戦・決勝を試合順でソートして返す。
    """
    matches = (
        db.query(Match)
        .options(
            joinedload(Match.home_team),
            joinedload(Match.away_team),
            joinedload(Match.venue),
        )
        .filter(
            Match.tournament_id == tournament_id,
            Match.stage.in_([MatchStage.SEMIFINAL, MatchStage.THIRD_PLACE, MatchStage.FINAL]),
        )
        .order_by(Match.match_order)
        .all()
    )

    return MatchList(matches=matches, total=len(matches))


@router.get("/check-played")
def check_teams_played(
    team1_id: int = Query(..., description="チーム1のID"),
    team2_id: int = Query(..., description="チーム2のID"),
    tournament_id: int = Query(..., description="大会ID"),
    db: Session = Depends(get_db),
):
    """
    2チームが予選リーグで対戦済みかチェック

    最終日の組み合わせで対戦済みチーム同士の組み合わせを警告するために使用。
    """
    # 予選リーグでの対戦を検索
    played_match = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.stage == MatchStage.PRELIMINARY,
        (
            ((Match.home_team_id == team1_id) & (Match.away_team_id == team2_id)) |
            ((Match.home_team_id == team2_id) & (Match.away_team_id == team1_id))
        )
    ).first()

    if played_match:
        # 対戦済みの場合、試合情報を返す
        return {
            "played": True,
            "match_id": played_match.id,
            "match_date": played_match.match_date.isoformat() if played_match.match_date else None,
            "home_score": played_match.home_score_total,
            "away_score": played_match.away_score_total,
            "message": "予選リーグで対戦済みです",
        }
    else:
        return {
            "played": False,
            "match_id": None,
            "match_date": None,
            "home_score": None,
            "away_score": None,
            "message": "未対戦です",
        }


@router.post("/swap-teams", response_model=SwapTeamsResponse)
def swap_teams(
    request: SwapTeamsRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    2つの試合間でチームを入れ替え（管理者専用）

    最終日の組み合わせ画面でドラッグ&ドロップによりチームを入れ替える際に使用。
    試合1の指定サイド(home/away)のチームと試合2の指定サイドのチームを交換する。
    """
    # 試合1を取得
    match1 = db.query(Match).filter(Match.id == request.match1_id).first()
    if not match1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"試合1が見つかりません (ID: {request.match1_id})"
        )

    # 試合2を取得
    match2 = db.query(Match).filter(Match.id == request.match2_id).first()
    if not match2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"試合2が見つかりません (ID: {request.match2_id})"
        )

    # ロック中かチェック
    if match1.is_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"試合1 (ID: {request.match1_id}) は現在編集中です"
        )
    if match2.is_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"試合2 (ID: {request.match2_id}) は現在編集中です"
        )

    # 完了済み試合は入れ替え不可
    if match1.status == MatchStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"試合1 (ID: {request.match1_id}) は既に完了しています"
        )
    if match2.status == MatchStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"試合2 (ID: {request.match2_id}) は既に完了しています"
        )

    # 試合1のチームIDを取得
    if request.side1 == "home":
        team1_id = match1.home_team_id
    else:
        team1_id = match1.away_team_id

    # 試合2のチームIDを取得
    if request.side2 == "home":
        team2_id = match2.home_team_id
    else:
        team2_id = match2.away_team_id

    # 同じチームの入れ替えは不要
    if team1_id == team2_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="同じチームを入れ替えることはできません"
        )

    # チームを入れ替え
    if request.side1 == "home":
        match1.home_team_id = team2_id
    else:
        match1.away_team_id = team2_id

    if request.side2 == "home":
        match2.home_team_id = team1_id
    else:
        match2.away_team_id = team1_id

    db.commit()

    return SwapTeamsResponse(
        message="チームを入れ替えました",
        match1_id=request.match1_id,
        match2_id=request.match2_id,
    )
