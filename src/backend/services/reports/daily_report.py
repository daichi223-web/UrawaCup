"""
日次試合結果報告書ジェネレータ

TournaMate_Report_Formats.md Section 2 に基づく

レイアウト:
- ヘッダー: 大会名、送信先、発信元
- 試合結果: 各試合のスコア、得点経過
- フッター: 運営事務局
"""

import io
from datetime import date
from typing import Optional, List

from sqlalchemy.orm import Session, joinedload

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle

from .base import BaseReportGenerator
from .types import (
    DailyReportData,
    MatchResultData,
    GoalData,
    SenderInfo,
    VenueInfo,
    TournamentInfo,
)

from models.tournament import Tournament
from models.match import Match, MatchStage, MatchStatus
from models.venue import Venue
from models.goal import Goal


class DailyReportGenerator(BaseReportGenerator):
    """
    日次試合結果報告書ジェネレータ

    毎日の試合終了後に生成される報告書。
    各会場の試合結果と得点経過を含む。
    """

    MAX_MATCHES_PER_PAGE = 4  # 1ページあたりの最大試合数

    def __init__(
        self,
        db: Session,
        tournament_id: int,
        target_date: date,
        venue_id: Optional[int] = None,
        sender: Optional[SenderInfo] = None,
    ):
        super().__init__(db)
        self.tournament_id = tournament_id
        self.target_date = target_date
        self.venue_id = venue_id
        self._explicit_sender = sender  # 明示的に渡された発信元

    def _get_sender(self, tournament: "Tournament") -> SenderInfo:
        """発信元情報を取得（優先順位: 引数 > Tournament設定 > デフォルト）"""
        if self._explicit_sender:
            return self._explicit_sender

        # Tournamentから取得
        if tournament.sender_organization and tournament.sender_name:
            return SenderInfo(
                organization=tournament.sender_organization,
                name=tournament.sender_name,
                contact=tournament.sender_contact or "",
            )

        # デフォルト
        return SenderInfo(
            organization="浦和カップ運営事務局",
            name="担当者",
            contact=""
        )

    def _load_data(self) -> DailyReportData:
        """報告書用データをDBから読み込み"""
        # 大会情報
        tournament = self.db.query(Tournament).filter(
            Tournament.id == self.tournament_id
        ).first()
        if not tournament:
            raise ValueError(f"大会が見つかりません (ID: {self.tournament_id})")

        # 会場情報
        venue = None
        if self.venue_id:
            venue = self.db.query(Venue).filter(Venue.id == self.venue_id).first()

        # 試合データ
        query = (
            self.db.query(Match)
            .options(
                joinedload(Match.home_team),
                joinedload(Match.away_team),
                joinedload(Match.venue),
                joinedload(Match.goals).joinedload(Goal.team),
            )
            .filter(
                Match.tournament_id == self.tournament_id,
                Match.match_date == self.target_date,
                Match.status == MatchStatus.COMPLETED,
                Match.stage != MatchStage.TRAINING,  # 研修試合は除外
            )
        )

        if self.venue_id:
            query = query.filter(Match.venue_id == self.venue_id)

        matches = query.order_by(Match.venue_id, Match.match_order).all()

        # データ変換
        match_results = []
        for match in matches:
            goals = []
            for goal in sorted(match.goals, key=lambda g: (g.half, g.minute)):
                goals.append(GoalData(
                    minute=goal.minute,
                    half=goal.half,
                    team_name=goal.team.name if goal.team else "Unknown",
                    scorer_name=goal.player_name,
                    is_own_goal=goal.is_own_goal,
                    is_penalty=goal.is_penalty,
                ))

            match_results.append(MatchResultData(
                match_number=match.match_order,
                kickoff_time=match.match_time.strftime("%H:%M") if match.match_time else "",
                home_team=match.home_team.short_name or match.home_team.name,
                away_team=match.away_team.short_name or match.away_team.name,
                home_score_half1=match.home_score_half1 or 0,
                home_score_half2=match.home_score_half2 or 0,
                away_score_half1=match.away_score_half1 or 0,
                away_score_half2=match.away_score_half2 or 0,
                has_penalty_shootout=match.has_penalty_shootout or False,
                home_pk=match.home_pk,
                away_pk=match.away_pk,
                goals=goals,
            ))

        # 日数計算
        day_number = 1
        if tournament.start_date:
            day_number = self._calculate_day_number(
                tournament.start_date, self.target_date
            )

        return DailyReportData(
            tournament=TournamentInfo(
                id=tournament.id,
                name=tournament.name,
                edition=tournament.edition or 0,
                start_date=tournament.start_date or self.target_date,
            ),
            report_date=self.target_date,
            day_number=day_number,
            venue=VenueInfo(
                id=venue.id if venue else 0,
                name=venue.name if venue else "全会場",
                group_id=venue.group_id if venue else None,
            ),
            sender=self._get_sender(tournament),
            recipients=[],  # 送信先は別途取得
            matches=match_results,
        )

    def generate(self, output_path: Optional[str] = None) -> io.BytesIO:
        """
        日次試合結果報告書を生成

        Returns:
            生成されたPDFのBytesIO
        """
        data = self._load_data()

        buffer = io.BytesIO()
        c = self._create_canvas(buffer)
        width, height = self.PAGE_SIZE

        # ヘッダー描画
        y = self._draw_report_header(c, data, height)

        # 試合結果描画
        for i, match in enumerate(data.matches):
            # 改ページチェック
            required_height = 50 * mm + len(match.goals) * 5 * mm
            y = self._new_page_if_needed(c, y, required_height)

            if y == height - self.MARGIN_TOP:
                # 新ページのヘッダー
                c.setFont(self._font_name, self.FONT_SIZE_BODY)
                c.drawString(self.MARGIN_LEFT, y, f"{data.tournament.name} - {data.report_date.isoformat()}")
                y -= 10 * mm

            y = self._draw_match_result(c, match, y)
            y -= 8 * mm

        # フッター
        self._draw_footer(c)

        c.save()
        buffer.seek(0)

        return buffer

    def _draw_report_header(self, c, data: DailyReportData, height: float) -> float:
        """報告書ヘッダーを描画"""
        width, _ = self.PAGE_SIZE
        y = height - self.MARGIN_TOP

        # タイトル
        c.setFont(self._font_name, self.FONT_SIZE_TITLE)
        title = f"{data.tournament.name} 試合結果報告書"
        c.drawString(self.MARGIN_LEFT, y, title)
        y -= 10 * mm

        # 発信元情報
        c.setFont(self._font_name, self.FONT_SIZE_BODY)
        c.drawString(self.MARGIN_LEFT, y, f"発信元：{data.sender.organization} {data.sender.name}")
        y -= 6 * mm

        if data.sender.contact:
            c.drawString(self.MARGIN_LEFT, y, f"連絡先：{data.sender.contact}")
            y -= 6 * mm

        y -= 4 * mm

        # 日付・会場
        c.drawString(self.MARGIN_LEFT, y, f"{data.report_date.isoformat()}（第{data.day_number}日）")
        y -= 6 * mm

        c.drawString(self.MARGIN_LEFT, y, f"大会会場：{data.venue.name}")
        y -= 10 * mm

        # 区切り線
        c.line(self.MARGIN_LEFT, y, width - self.MARGIN_RIGHT, y)
        y -= 8 * mm

        return y

    def _draw_match_result(self, c, match: MatchResultData, y: float) -> float:
        """試合結果を描画"""
        width, _ = self.PAGE_SIZE

        # 試合番号
        c.setFont(self._font_name, self.FONT_SIZE_BODY + 1)
        c.drawString(self.MARGIN_LEFT, y, f"第{match.match_number}試合")
        y -= 8 * mm

        # スコア
        c.setFont(self._font_name, self.FONT_SIZE_BODY)

        # チーム名とスコア
        score_text = f"  {match.home_team}  {match.home_score_total} - {match.away_score_total}  {match.away_team}"
        c.drawString(self.MARGIN_LEFT + 5 * mm, y, score_text)
        y -= 6 * mm

        # 前後半スコア
        c.setFont(self._font_name, self.FONT_SIZE_TABLE)
        half_score = f"     {match.home_score_half1} 前半 {match.away_score_half1}"
        c.drawString(self.MARGIN_LEFT + 10 * mm, y, half_score)
        y -= 5 * mm

        half_score = f"     {match.home_score_half2} 後半 {match.away_score_half2}"
        c.drawString(self.MARGIN_LEFT + 10 * mm, y, half_score)
        y -= 5 * mm

        # PK戦
        if match.has_penalty_shootout:
            pk_score = f"     {match.home_pk} PK {match.away_pk}"
            c.drawString(self.MARGIN_LEFT + 10 * mm, y, pk_score)
            y -= 5 * mm

        # 得点経過
        if match.goals:
            y -= 3 * mm
            c.setFont(self._font_name, self.FONT_SIZE_TABLE)
            c.drawString(self.MARGIN_LEFT + 5 * mm, y, "得点経過")
            y -= 5 * mm

            # 得点テーブル
            goal_data = [["時間", "チーム", "得点者名"]]
            for goal in match.goals:
                half_text = "前" if goal.half == 1 else "後"
                time_text = f"{half_text}{goal.minute}'"
                scorer = goal.scorer_name
                if goal.is_own_goal:
                    scorer += " (OG)"
                if goal.is_penalty:
                    scorer += " (PK)"
                goal_data.append([time_text, goal.team_name, scorer])

            # テーブル描画
            for row in goal_data:
                c.drawString(self.MARGIN_LEFT + 10 * mm, y, f"  {row[0]:>6}  {row[1]:<12}  {row[2]}")
                y -= 4 * mm

        return y


def generate_daily_report(
    db: Session,
    tournament_id: int,
    target_date: date,
    venue_id: Optional[int] = None,
    sender: Optional[SenderInfo] = None,
) -> io.BytesIO:
    """
    日次試合結果報告書を生成するヘルパー関数

    Args:
        db: データベースセッション
        tournament_id: 大会ID
        target_date: 対象日
        venue_id: 会場ID（省略時は全会場）
        sender: 発信元情報

    Returns:
        生成されたPDFのBytesIO
    """
    generator = DailyReportGenerator(
        db=db,
        tournament_id=tournament_id,
        target_date=target_date,
        venue_id=venue_id,
        sender=sender,
    )
    return generator.generate()
