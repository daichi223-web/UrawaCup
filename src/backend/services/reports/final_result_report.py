"""
最終結果報告書ジェネレータ

TournaMate_Report_Formats.md Section 4 に基づく

レイアウト:
- 順位決定戦結果（準決勝、3決、決勝）
- 最終順位（1-4位）
- 優秀選手一覧
- 研修試合結果（オプション）
"""

import io
from datetime import date
from typing import Optional, List

from sqlalchemy.orm import Session, joinedload

from reportlab.lib import colors
from reportlab.lib.units import mm

from .base import BaseReportGenerator
from .types import (
    TournamentInfo,
    KnockoutMatch,
    FinalRanking,
    OutstandingPlayer,
    MatchResultData,
    GoalData,
    FinalReportData,
)

from models.tournament import Tournament
from models.match import Match, MatchStage, MatchStatus
from models.goal import Goal
from models.tournament_award import (
    TournamentFinalRanking as DBFinalRanking,
    OutstandingPlayer as DBOutstandingPlayer,
    AwardType,
)


class FinalResultReportGenerator(BaseReportGenerator):
    """
    最終結果報告書ジェネレータ

    大会終了後に生成される最終結果報告書。
    決勝トーナメントの結果、最終順位、優秀選手を含む。
    """

    def __init__(
        self,
        db: Session,
        tournament_id: int,
        final_rankings: Optional[List[FinalRanking]] = None,
        outstanding_players: Optional[List[OutstandingPlayer]] = None,
    ):
        super().__init__(db)
        self.tournament_id = tournament_id
        self._explicit_rankings = final_rankings
        self._explicit_players = outstanding_players

    def _load_rankings(self) -> List[FinalRanking]:
        """最終順位を取得（優先順位: 引数 > DB）"""
        if self._explicit_rankings:
            return self._explicit_rankings

        # DBから取得
        db_rankings = (
            self.db.query(DBFinalRanking)
            .filter(DBFinalRanking.tournament_id == self.tournament_id)
            .order_by(DBFinalRanking.rank)
            .all()
        )

        return [
            FinalRanking(
                rank=r.rank,
                team_name=r.team.short_name or r.team.name if r.team else "Unknown",
            )
            for r in db_rankings
        ]

    def _load_outstanding_players(self) -> List[OutstandingPlayer]:
        """優秀選手を取得（優先順位: 引数 > DB）"""
        if self._explicit_players:
            return self._explicit_players

        # DBから取得
        db_players = (
            self.db.query(DBOutstandingPlayer)
            .filter(DBOutstandingPlayer.tournament_id == self.tournament_id)
            .order_by(DBOutstandingPlayer.award_type, DBOutstandingPlayer.id)
            .all()
        )

        return [
            OutstandingPlayer(
                award=p.award_display,
                player_name=p.player_name,
                team_name=p.team.short_name or p.team.name if p.team else "Unknown",
            )
            for p in db_players
        ]

    def _load_data(self) -> FinalReportData:
        """報告書用データをDBから読み込み"""
        # 大会情報
        tournament = self.db.query(Tournament).filter(
            Tournament.id == self.tournament_id
        ).first()
        if not tournament:
            raise ValueError(f"大会が見つかりません (ID: {self.tournament_id})")

        # 決勝トーナメント試合を取得
        knockout_stages = [
            MatchStage.SEMIFINAL,
            MatchStage.THIRD_PLACE,
            MatchStage.FINAL,
        ]

        matches = (
            self.db.query(Match)
            .options(
                joinedload(Match.home_team),
                joinedload(Match.away_team),
            )
            .filter(
                Match.tournament_id == self.tournament_id,
                Match.stage.in_(knockout_stages),
                Match.status == MatchStatus.COMPLETED,
            )
            .order_by(Match.match_date, Match.match_order)
            .all()
        )

        knockout_results = []
        for match in matches:
            round_name = self._get_round_name(match.stage, match.match_order)
            home_seed = self._get_seed_name(match, is_home=True)
            away_seed = self._get_seed_name(match, is_home=False)

            knockout_results.append(KnockoutMatch(
                round_name=round_name,
                home_seed=home_seed,
                home_team=match.home_team.short_name or match.home_team.name if match.home_team else "TBD",
                away_seed=away_seed,
                away_team=match.away_team.short_name or match.away_team.name if match.away_team else "TBD",
                home_score_half1=match.home_score_half1 or 0,
                home_score_half2=match.home_score_half2 or 0,
                away_score_half1=match.away_score_half1 or 0,
                away_score_half2=match.away_score_half2 or 0,
                has_penalty_shootout=match.has_penalty_shootout or False,
                home_pk=match.home_pk,
                away_pk=match.away_pk,
            ))

        # 研修試合を取得
        training_matches = (
            self.db.query(Match)
            .options(
                joinedload(Match.home_team),
                joinedload(Match.away_team),
                joinedload(Match.venue),
                joinedload(Match.goals).joinedload(Goal.team),
            )
            .filter(
                Match.tournament_id == self.tournament_id,
                Match.stage == MatchStage.TRAINING,
                Match.status == MatchStatus.COMPLETED,
            )
            .order_by(Match.venue_id, Match.match_order)
            .all()
        )

        training_results = []
        for match in training_matches:
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

            training_results.append(MatchResultData(
                match_number=match.match_order,
                kickoff_time=match.match_time.strftime("%H:%M") if match.match_time else "",
                home_team=match.home_team.short_name or match.home_team.name if match.home_team else "",
                away_team=match.away_team.short_name or match.away_team.name if match.away_team else "",
                home_score_half1=match.home_score_half1 or 0,
                home_score_half2=match.home_score_half2 or 0,
                away_score_half1=match.away_score_half1 or 0,
                away_score_half2=match.away_score_half2 or 0,
                has_penalty_shootout=match.has_penalty_shootout or False,
                home_pk=match.home_pk,
                away_pk=match.away_pk,
                goals=goals,
            ))

        return FinalReportData(
            tournament=TournamentInfo(
                id=tournament.id,
                name=tournament.name,
                edition=tournament.edition or 0,
                start_date=tournament.start_date or date.today(),
            ),
            knockout_results=knockout_results,
            final_rankings=self._load_rankings(),
            outstanding_players=self._load_outstanding_players(),
            training_matches=training_results,
        )

    def _get_round_name(self, stage: MatchStage, match_order: int) -> str:
        """ラウンド名を取得"""
        if stage == MatchStage.SEMIFINAL:
            return f"準決勝{match_order}"
        elif stage == MatchStage.THIRD_PLACE:
            return "3位決定戦"
        elif stage == MatchStage.FINAL:
            return "決勝"
        return ""

    def _get_seed_name(self, match: Match, is_home: bool) -> str:
        """シード名を取得（例：A1位）"""
        if is_home:
            return match.home_seed or ""
        else:
            return match.away_seed or ""

    def generate(self, output_path: Optional[str] = None) -> io.BytesIO:
        """
        最終結果報告書を生成

        Returns:
            生成されたPDFのBytesIO
        """
        data = self._load_data()

        buffer = io.BytesIO()
        c = self._create_canvas(buffer)
        width, height = self.PAGE_SIZE

        y = height - self.MARGIN_TOP

        # タイトル
        c.setFont(self._font_name, self.FONT_SIZE_TITLE)
        c.drawString(self.MARGIN_LEFT, y, f"{data.tournament.name} 組合せ及び日程表")
        y -= 8 * mm

        c.setFont(self._font_name, self.FONT_SIZE_BODY)
        final_date = data.tournament.start_date  # Issue: 最終日の日付取得方法
        c.drawString(self.MARGIN_LEFT, y, final_date.strftime("%Y年%m月%d日"))
        y -= 12 * mm

        # 順位決定戦セクション
        c.setFont(self._font_name, self.FONT_SIZE_BODY + 1)
        c.drawString(self.MARGIN_LEFT, y, "☆順位決定戦")
        y -= 10 * mm

        for match in data.knockout_results:
            y = self._new_page_if_needed(c, y, 35 * mm)
            y = self._draw_knockout_match(c, match, y)
            y -= 8 * mm

        # 最終順位セクション
        y = self._new_page_if_needed(c, y, 50 * mm)

        c.setFont(self._font_name, self.FONT_SIZE_BODY + 1)
        c.drawString(self.MARGIN_LEFT, y, "☆最終順位")
        y -= 8 * mm

        if data.final_rankings:
            y = self._draw_rankings_table(c, data.final_rankings, y)
        else:
            c.setFont(self._font_name, self.FONT_SIZE_TABLE)
            c.drawString(self.MARGIN_LEFT + 10 * mm, y, "（データなし）")
            y -= 6 * mm

        y -= 8 * mm

        # 優秀選手セクション
        y = self._new_page_if_needed(c, y, 60 * mm)

        c.setFont(self._font_name, self.FONT_SIZE_BODY + 1)
        c.drawString(self.MARGIN_LEFT, y, "☆優秀選手")
        y -= 8 * mm

        if data.outstanding_players:
            y = self._draw_players_table(c, data.outstanding_players, y)
        else:
            c.setFont(self._font_name, self.FONT_SIZE_TABLE)
            c.drawString(self.MARGIN_LEFT + 10 * mm, y, "（データなし）")
            y -= 6 * mm

        # 研修試合セクション
        if data.training_matches:
            y = self._new_page_if_needed(c, y, 40 * mm)

            c.setFont(self._font_name, self.FONT_SIZE_BODY + 1)
            c.drawString(self.MARGIN_LEFT, y, "☆研修試合結果")
            y -= 8 * mm

            y = self._draw_training_matches(c, data.training_matches, y)

        # フッター
        self._draw_footer(c)

        c.save()
        buffer.seek(0)

        return buffer

    def _draw_knockout_match(self, c, match: KnockoutMatch, y: float) -> float:
        """ノックアウト試合を描画"""
        c.setFont(self._font_name, self.FONT_SIZE_BODY)
        c.drawString(self.MARGIN_LEFT + 5 * mm, y, match.round_name)
        y -= 7 * mm

        # スコア表示
        c.setFont(self._font_name, self.FONT_SIZE_TABLE)
        home_total = match.home_score_half1 + match.home_score_half2
        away_total = match.away_score_half1 + match.away_score_half2

        # シード付きチーム名
        home_display = f"{match.home_seed}({match.home_team})" if match.home_seed else match.home_team
        away_display = f"{match.away_seed}({match.away_team})" if match.away_seed else match.away_team

        score_line = f"  {home_display}  {home_total} - {away_total}  {away_display}"
        c.drawString(self.MARGIN_LEFT + 10 * mm, y, score_line)
        y -= 5 * mm

        # 前後半スコア
        half_line = f"            {match.home_score_half1} 前半 {match.away_score_half1}"
        c.drawString(self.MARGIN_LEFT + 10 * mm, y, half_line)
        y -= 4 * mm

        half_line = f"            {match.home_score_half2} 後半 {match.away_score_half2}"
        c.drawString(self.MARGIN_LEFT + 10 * mm, y, half_line)
        y -= 4 * mm

        # PK戦
        if match.has_penalty_shootout:
            pk_line = f"            {match.home_pk} PK {match.away_pk}"
            c.drawString(self.MARGIN_LEFT + 10 * mm, y, pk_line)
            y -= 4 * mm

        return y

    def _draw_rankings_table(self, c, rankings: List[FinalRanking], y: float) -> float:
        """順位テーブルを描画"""
        c.setFont(self._font_name, self.FONT_SIZE_TABLE)

        # ヘッダー
        c.drawString(self.MARGIN_LEFT + 10 * mm, y, "順位")
        c.drawString(self.MARGIN_LEFT + 35 * mm, y, "チーム名")
        y -= 5 * mm

        # 区切り線
        width, _ = self.PAGE_SIZE
        c.line(self.MARGIN_LEFT + 5 * mm, y + 2 * mm, self.MARGIN_LEFT + 120 * mm, y + 2 * mm)

        # データ
        for ranking in sorted(rankings, key=lambda r: r.rank):
            c.drawString(self.MARGIN_LEFT + 10 * mm, y, f"{ranking.rank}位")
            c.drawString(self.MARGIN_LEFT + 35 * mm, y, ranking.team_name)
            y -= 5 * mm

        return y

    def _draw_players_table(self, c, players: List[OutstandingPlayer], y: float) -> float:
        """優秀選手テーブルを描画"""
        c.setFont(self._font_name, self.FONT_SIZE_TABLE)

        # ヘッダー
        c.drawString(self.MARGIN_LEFT + 10 * mm, y, "賞")
        c.drawString(self.MARGIN_LEFT + 45 * mm, y, "名前")
        c.drawString(self.MARGIN_LEFT + 95 * mm, y, "チーム名")
        y -= 5 * mm

        # 区切り線
        c.line(self.MARGIN_LEFT + 5 * mm, y + 2 * mm, self.MARGIN_LEFT + 150 * mm, y + 2 * mm)

        # データ
        for player in players:
            c.drawString(self.MARGIN_LEFT + 10 * mm, y, player.award)
            c.drawString(self.MARGIN_LEFT + 45 * mm, y, player.player_name)
            c.drawString(self.MARGIN_LEFT + 95 * mm, y, player.team_name)
            y -= 5 * mm

        return y

    def _draw_training_matches(self, c, matches: List[MatchResultData], y: float) -> float:
        """研修試合一覧を描画"""
        c.setFont(self._font_name, self.FONT_SIZE_TABLE)

        # ヘッダー
        c.drawString(self.MARGIN_LEFT + 10 * mm, y, "No")
        c.drawString(self.MARGIN_LEFT + 25 * mm, y, "ホーム")
        c.drawString(self.MARGIN_LEFT + 70 * mm, y, "スコア")
        c.drawString(self.MARGIN_LEFT + 100 * mm, y, "アウェイ")
        y -= 5 * mm

        # 区切り線
        c.line(self.MARGIN_LEFT + 5 * mm, y + 2 * mm, self.MARGIN_LEFT + 150 * mm, y + 2 * mm)

        # データ
        for match in matches:
            score = f"{match.home_score_total} - {match.away_score_total}"
            half_score = f"({match.home_score_half1}-{match.away_score_half1}/{match.home_score_half2}-{match.away_score_half2})"

            c.drawString(self.MARGIN_LEFT + 10 * mm, y, str(match.match_number))
            c.drawString(self.MARGIN_LEFT + 25 * mm, y, match.home_team)
            c.drawString(self.MARGIN_LEFT + 70 * mm, y, score)
            c.drawString(self.MARGIN_LEFT + 100 * mm, y, match.away_team)
            y -= 4 * mm

            c.drawString(self.MARGIN_LEFT + 70 * mm, y, half_score)
            if match.has_penalty_shootout:
                c.drawString(self.MARGIN_LEFT + 110 * mm, y, f"PK {match.home_pk}-{match.away_pk}")
            y -= 5 * mm

        return y


def generate_final_result_report(
    db: Session,
    tournament_id: int,
    final_rankings: Optional[List[FinalRanking]] = None,
    outstanding_players: Optional[List[OutstandingPlayer]] = None,
) -> io.BytesIO:
    """
    最終結果報告書を生成するヘルパー関数

    Args:
        db: データベースセッション
        tournament_id: 大会ID
        final_rankings: 最終順位リスト
        outstanding_players: 優秀選手リスト

    Returns:
        生成されたPDFのBytesIO
    """
    generator = FinalResultReportGenerator(
        db=db,
        tournament_id=tournament_id,
        final_rankings=final_rankings,
        outstanding_players=outstanding_players,
    )
    return generator.generate()
