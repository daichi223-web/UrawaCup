"""
最終日組み合わせ表ジェネレータ

TournaMate_Report_Formats.md Section 3 に基づく

レイアウト:
- 順位リーグ会場ごとの試合スケジュール
- 3決・決勝戦のスケジュール
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
    TournamentInfo,
    FinalDayMatch,
    FinalDayVenueSchedule,
    FinalDayScheduleData,
)

from models.tournament import Tournament
from models.match import Match, MatchStage, MatchStatus
from models.venue import Venue


class FinalDayScheduleGenerator(BaseReportGenerator):
    """
    最終日組み合わせ表ジェネレータ

    予選終了後に生成される最終日の組み合わせ表。
    順位リーグと決勝トーナメントの試合スケジュールを含む。
    """

    def __init__(
        self,
        db: Session,
        tournament_id: int,
        target_date: date,
    ):
        super().__init__(db)
        self.tournament_id = tournament_id
        self.target_date = target_date

    def _load_data(self) -> FinalDayScheduleData:
        """報告書用データをDBから読み込み"""
        # 大会情報
        tournament = self.db.query(Tournament).filter(
            Tournament.id == self.tournament_id
        ).first()
        if not tournament:
            raise ValueError(f"大会が見つかりません (ID: {self.tournament_id})")

        # 会場ごとの試合データを取得
        matches = (
            self.db.query(Match)
            .options(
                joinedload(Match.home_team),
                joinedload(Match.away_team),
                joinedload(Match.venue).joinedload(Venue.manager_team),
            )
            .filter(
                Match.tournament_id == self.tournament_id,
                Match.match_date == self.target_date,
            )
            .order_by(Match.venue_id, Match.match_order)
            .all()
        )

        # 会場ごとにグループ化
        venue_matches = {}
        knockout_matches = []

        for match in matches:
            venue_id = match.venue_id

            match_data = FinalDayMatch(
                match_number=match.match_order,
                kickoff_time=match.match_time.strftime("%H:%M") if match.match_time else "",
                home_team=match.home_team.short_name or match.home_team.name if match.home_team else "TBD",
                away_team=match.away_team.short_name or match.away_team.name if match.away_team else "TBD",
                match_type=self._get_match_type(match.stage),
                referee_main="当該",
                referee_assistant="当該",
            )

            # 決勝トーナメント試合は別リストへ
            if match.stage in [MatchStage.SEMIFINAL, MatchStage.THIRD_PLACE, MatchStage.FINAL]:
                knockout_matches.append((match, match_data))
            else:
                if venue_id not in venue_matches:
                    venue_matches[venue_id] = {
                        'venue': match.venue,
                        'matches': []
                    }
                venue_matches[venue_id]['matches'].append(match_data)

        # 順位リーグの会場スケジュール
        ranking_venues = []
        for venue_id, data in venue_matches.items():
            venue = data['venue']
            # 会場責任チームを取得（manager_team > 会場名から推測 > 空）
            manager_name = ""
            if venue and venue.manager_team:
                manager_name = venue.manager_team.short_name or venue.manager_team.name
            ranking_venues.append(FinalDayVenueSchedule(
                venue_name=venue.name if venue else "不明",
                venue_manager=manager_name,
                matches=data['matches'],
            ))

        # 3決・決勝戦の会場スケジュール
        knockout_venue = None
        if knockout_matches:
            # 最初のノックアウト試合の会場を使用
            first_match = knockout_matches[0][0]
            venue = first_match.venue
            manager_name = ""
            if venue and venue.manager_team:
                manager_name = venue.manager_team.short_name or venue.manager_team.name
            knockout_venue = FinalDayVenueSchedule(
                venue_name=venue.name if venue else "駒場スタジアム",
                venue_manager=manager_name,
                matches=[m[1] for m in knockout_matches],
            )
        else:
            # ダミーデータ
            knockout_venue = FinalDayVenueSchedule(
                venue_name="駒場スタジアム",
                venue_manager="",
                matches=[],
            )

        return FinalDayScheduleData(
            date=self.target_date,
            ranking_league_venues=ranking_venues,
            knockout_venue=knockout_venue,
        )

    def _get_match_type(self, stage: MatchStage) -> Optional[str]:
        """ステージから試合タイプを取得"""
        type_map = {
            MatchStage.SEMIFINAL: "準決勝",
            MatchStage.THIRD_PLACE: "3位決",
            MatchStage.FINAL: "決勝",
            MatchStage.TRAINING: "研修",
        }
        return type_map.get(stage)

    def generate(self, output_path: Optional[str] = None) -> io.BytesIO:
        """
        最終日組み合わせ表を生成

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
        date_str = data.date.strftime("%m月%d日")
        weekday = ["月", "火", "水", "木", "金", "土", "日"][data.date.weekday()]
        c.drawString(self.MARGIN_LEFT, y, f"{date_str}（{weekday}）【順位リーグ】")
        y -= 12 * mm

        # 順位リーグ各会場
        for venue_schedule in data.ranking_league_venues:
            y = self._new_page_if_needed(c, y, 60 * mm)

            c.setFont(self._font_name, self.FONT_SIZE_BODY + 1)
            c.drawString(self.MARGIN_LEFT, y, f"【{venue_schedule.venue_name}】")
            y -= 8 * mm

            # 試合テーブル
            y = self._draw_schedule_table(c, venue_schedule.matches, y)
            y -= 10 * mm

        # 3決・決勝戦セクション
        y = self._new_page_if_needed(c, y, 80 * mm)

        c.setFont(self._font_name, self.FONT_SIZE_TITLE)
        c.drawString(self.MARGIN_LEFT, y, f"{date_str}（{weekday}）【3決・決勝戦】")
        y -= 12 * mm

        c.setFont(self._font_name, self.FONT_SIZE_BODY + 1)
        c.drawString(self.MARGIN_LEFT, y, f"【{data.knockout_venue.venue_name}】")
        y -= 8 * mm

        # 3決・決勝テーブル
        if data.knockout_venue.matches:
            y = self._draw_knockout_table(c, data.knockout_venue.matches, y)

        # フッター
        self._draw_footer(c)

        c.save()
        buffer.seek(0)

        return buffer

    def _draw_schedule_table(self, c, matches: List[FinalDayMatch], y: float) -> float:
        """スケジュールテーブルを描画"""
        c.setFont(self._font_name, self.FONT_SIZE_TABLE)

        # ヘッダー
        c.drawString(self.MARGIN_LEFT + 5 * mm, y, "KO")
        c.drawString(self.MARGIN_LEFT + 25 * mm, y, "対戦")
        y -= 5 * mm

        # 区切り線
        width, _ = self.PAGE_SIZE
        c.line(self.MARGIN_LEFT, y + 2 * mm, width - self.MARGIN_RIGHT, y + 2 * mm)

        # 試合データ
        for match in matches:
            c.drawString(self.MARGIN_LEFT + 5 * mm, y, match.kickoff_time)
            c.drawString(self.MARGIN_LEFT + 25 * mm, y, f"{match.home_team} vs {match.away_team}")
            y -= 5 * mm

        return y

    def _draw_knockout_table(self, c, matches: List[FinalDayMatch], y: float) -> float:
        """3決・決勝テーブルを描画"""
        c.setFont(self._font_name, self.FONT_SIZE_TABLE)

        # ヘッダー
        c.drawString(self.MARGIN_LEFT + 5 * mm, y, "KO")
        c.drawString(self.MARGIN_LEFT + 25 * mm, y, "対戦")
        c.drawString(self.MARGIN_LEFT + 100 * mm, y, "審判")
        y -= 5 * mm

        # 区切り線
        width, _ = self.PAGE_SIZE
        c.line(self.MARGIN_LEFT, y + 2 * mm, width - self.MARGIN_RIGHT, y + 2 * mm)

        # 試合データ
        for match in matches:
            type_prefix = f"[{match.match_type}] " if match.match_type else ""
            c.drawString(self.MARGIN_LEFT + 5 * mm, y, match.kickoff_time)
            c.drawString(self.MARGIN_LEFT + 25 * mm, y, f"{type_prefix}{match.home_team} vs {match.away_team}")
            c.drawString(self.MARGIN_LEFT + 100 * mm, y, f"主審：{match.referee_main} 副審：{match.referee_assistant}")
            y -= 5 * mm

        return y


def generate_final_day_schedule(
    db: Session,
    tournament_id: int,
    target_date: date,
) -> io.BytesIO:
    """
    最終日組み合わせ表を生成するヘルパー関数

    Args:
        db: データベースセッション
        tournament_id: 大会ID
        target_date: 対象日

    Returns:
        生成されたPDFのBytesIO
    """
    generator = FinalDayScheduleGenerator(
        db=db,
        tournament_id=tournament_id,
        target_date=target_date,
    )
    return generator.generate()
