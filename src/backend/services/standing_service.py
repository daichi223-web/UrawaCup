"""
StandingService - 順位表計算サービス

順位決定ルール（優先順位）:
1. 勝点（勝利=3点、引分=1点、敗北=0点）
2. 得失点差
3. 総得点
4. 当該チーム間の対戦成績
5. 抽選
"""

from typing import List, Dict, Tuple
from sqlalchemy.orm import Session

from models.standing import Standing
from models.match import Match, MatchStage, MatchStatus, MatchResult
from models.team import Team


class StandingService:
    """順位表計算サービス"""

    def __init__(self, db: Session):
        self.db = db

    def update_group_standings(self, tournament_id: int, group_id: str) -> List[Standing]:
        """
        グループの順位表を更新

        試合結果に基づいて順位表を再計算し、DBに保存する
        """
        # グループ内のチームを取得
        teams = self.db.query(Team).filter(
            Team.tournament_id == tournament_id,
            Team.group_id == group_id,
        ).all()

        team_ids = [t.id for t in teams]

        # 完了した予選リーグの試合を取得
        matches = self.db.query(Match).filter(
            Match.tournament_id == tournament_id,
            Match.group_id == group_id,
            Match.stage == MatchStage.PRELIMINARY,
            Match.status == MatchStatus.COMPLETED,
        ).all()

        # 各チームの成績を計算
        stats = {tid: self._create_empty_stats() for tid in team_ids}

        for match in matches:
            self._update_stats_from_match(stats, match)

        # 順位表レコードを取得または作成
        standings = {}
        for team in teams:
            standing = self.db.query(Standing).filter(
                Standing.tournament_id == tournament_id,
                Standing.group_id == group_id,
                Standing.team_id == team.id,
            ).first()

            if not standing:
                standing = Standing(
                    tournament_id=tournament_id,
                    group_id=group_id,
                    team_id=team.id,
                )
                self.db.add(standing)

            # 成績を更新
            team_stats = stats[team.id]
            standing.played = team_stats["played"]
            standing.won = team_stats["won"]
            standing.drawn = team_stats["drawn"]
            standing.lost = team_stats["lost"]
            standing.goals_for = team_stats["goals_for"]
            standing.goals_against = team_stats["goals_against"]
            standing.calculate_derived_values()

            standings[team.id] = standing

        self.db.flush()

        # 順位を決定
        self._determine_ranks(standings, matches)

        self.db.commit()

        return list(standings.values())

    def _create_empty_stats(self) -> Dict:
        """空の成績辞書を作成"""
        return {
            "played": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
            "goals_for": 0,
            "goals_against": 0,
        }

    def _update_stats_from_match(self, stats: Dict, match: Match):
        """試合結果から成績を更新"""
        home_id = match.home_team_id
        away_id = match.away_team_id

        if home_id not in stats or away_id not in stats:
            return

        # 試合数
        stats[home_id]["played"] += 1
        stats[away_id]["played"] += 1

        # 得点・失点
        home_goals = match.home_score_total or 0
        away_goals = match.away_score_total or 0

        stats[home_id]["goals_for"] += home_goals
        stats[home_id]["goals_against"] += away_goals
        stats[away_id]["goals_for"] += away_goals
        stats[away_id]["goals_against"] += home_goals

        # 勝敗
        if match.result == MatchResult.HOME_WIN:
            stats[home_id]["won"] += 1
            stats[away_id]["lost"] += 1
        elif match.result == MatchResult.AWAY_WIN:
            stats[away_id]["won"] += 1
            stats[home_id]["lost"] += 1
        else:  # DRAW
            stats[home_id]["drawn"] += 1
            stats[away_id]["drawn"] += 1

    def _determine_ranks(self, standings: Dict[int, Standing], matches: List[Match]):
        """
        順位を決定

        順位決定ルール:
        1. 勝点
        2. 得失点差
        3. 総得点
        4. 当該チーム間の対戦成績
        5. 抽選（未実装、同順位のまま）
        """
        # 対戦成績の辞書を作成
        head_to_head = self._build_head_to_head(matches)

        # ソート用のキー関数
        def sort_key(standing: Standing) -> Tuple:
            return (
                -standing.points,          # 勝点（降順）
                -standing.goal_difference, # 得失点差（降順）
                -standing.goals_for,       # 総得点（降順）
            )

        # まず基本的なソート
        sorted_standings = sorted(standings.values(), key=sort_key)

        # 同勝点・同得失点差・同総得点のチームグループを識別して直接対決で順位付け
        current_rank = 1
        i = 0
        while i < len(sorted_standings):
            # 同じ成績のチームを集める
            same_stats = [sorted_standings[i]]
            j = i + 1
            while j < len(sorted_standings):
                if sort_key(sorted_standings[j]) == sort_key(sorted_standings[i]):
                    same_stats.append(sorted_standings[j])
                    j += 1
                else:
                    break

            if len(same_stats) == 1:
                # 1チームのみ
                same_stats[0].rank = current_rank
                same_stats[0].rank_reason = None
            else:
                # 複数チームで同成績 → 直接対決で順位付け
                self._resolve_by_head_to_head(same_stats, head_to_head, current_rank)

            current_rank += len(same_stats)
            i = j

    def _build_head_to_head(self, matches: List[Match]) -> Dict[Tuple[int, int], Dict]:
        """直接対決の成績辞書を作成"""
        h2h = {}

        for match in matches:
            home_id = match.home_team_id
            away_id = match.away_team_id
            home_goals = match.home_score_total or 0
            away_goals = match.away_score_total or 0

            # 双方向で記録
            for t1, t2, g1, g2 in [(home_id, away_id, home_goals, away_goals),
                                     (away_id, home_id, away_goals, home_goals)]:
                key = (t1, t2)
                if key not in h2h:
                    h2h[key] = {"wins": 0, "draws": 0, "losses": 0, "gf": 0, "ga": 0}

                h2h[key]["gf"] += g1
                h2h[key]["ga"] += g2

                if g1 > g2:
                    h2h[key]["wins"] += 1
                elif g1 < g2:
                    h2h[key]["losses"] += 1
                else:
                    h2h[key]["draws"] += 1

        return h2h

    def _resolve_by_head_to_head(
        self,
        standings: List[Standing],
        head_to_head: Dict[Tuple[int, int], Dict],
        start_rank: int
    ):
        """直接対決で順位を決定"""
        if len(standings) == 2:
            # 2チームの場合
            t1 = standings[0].team_id
            t2 = standings[1].team_id

            key = (t1, t2)
            if key in head_to_head:
                h2h = head_to_head[key]
                if h2h["wins"] > h2h["losses"]:
                    # t1が上位
                    standings[0].rank = start_rank
                    standings[1].rank = start_rank + 1
                    standings[0].rank_reason = "直接対決で上位"
                    standings[1].rank_reason = "直接対決で下位"
                    return
                elif h2h["wins"] < h2h["losses"]:
                    # t2が上位
                    standings[0].rank = start_rank + 1
                    standings[1].rank = start_rank
                    standings[0].rank_reason = "直接対決で下位"
                    standings[1].rank_reason = "直接対決で上位"
                    return
                else:
                    # 直接対決も同成績 → 得失点差で判定
                    if h2h["gf"] - h2h["ga"] > head_to_head[(t2, t1)]["gf"] - head_to_head[(t2, t1)]["ga"]:
                        standings[0].rank = start_rank
                        standings[1].rank = start_rank + 1
                        standings[0].rank_reason = "直接対決の得失点差で上位"
                        standings[1].rank_reason = "直接対決の得失点差で下位"
                        return
                    elif h2h["gf"] - h2h["ga"] < head_to_head[(t2, t1)]["gf"] - head_to_head[(t2, t1)]["ga"]:
                        standings[0].rank = start_rank + 1
                        standings[1].rank = start_rank
                        standings[0].rank_reason = "直接対決の得失点差で下位"
                        standings[1].rank_reason = "直接対決の得失点差で上位"
                        return

        # 3チーム以上、または決着がつかない場合は同順位（将来的には抽選）
        for idx, standing in enumerate(standings):
            standing.rank = start_rank + idx
            standing.rank_reason = "同成績（抽選待ち）" if len(standings) > 1 else None

    def get_group_first_place(self, tournament_id: int, group_id: str) -> Standing:
        """グループ1位のチームを取得"""
        return self.db.query(Standing).filter(
            Standing.tournament_id == tournament_id,
            Standing.group_id == group_id,
            Standing.rank == 1,
        ).first()

    def get_teams_by_rank(self, tournament_id: int, rank: int) -> List[Standing]:
        """指定順位のチームを全グループから取得"""
        return self.db.query(Standing).filter(
            Standing.tournament_id == tournament_id,
            Standing.rank == rank,
        ).order_by(Standing.group_id).all()

    def calculate_overall_standings(self, tournament_id: int) -> List[Standing]:
        """
        全体順位を計算（順位リーグ用）

        ソート順序:
        1. グループ内順位
        2. 勝点
        3. 得失点差
        4. 総得点
        5. ランダム（同成績の場合）

        Returns:
            全チームを全体順位順にソートしたリスト
        """
        import random

        standings = self.db.query(Standing).filter(
            Standing.tournament_id == tournament_id,
        ).all()

        # ソート用のキー関数（同成績時はランダム要素を追加）
        def sort_key(s: Standing) -> Tuple:
            return (
                s.rank,                    # グループ内順位（昇順）
                -s.points,                 # 勝点（降順）
                -s.goal_difference,        # 得失点差（降順）
                -s.goals_for,              # 総得点（降順）
                random.random(),           # 同成績時のランダム決定
            )

        sorted_standings = sorted(standings, key=sort_key)

        # 全体順位を付与
        for idx, standing in enumerate(sorted_standings):
            standing.overall_rank = idx + 1

        return sorted_standings

    def get_position_league_teams(self, tournament_id: int) -> Tuple[List[Standing], List[List[Standing]], List[Dict]]:
        """
        順位リーグ用のチーム振り分けを計算

        Returns:
            (knockout_teams, position_leagues, warnings)
            - knockout_teams: 決勝T進出チーム（各グループ1位）
            - position_leagues: 4つの順位リーグ（それぞれチームのリスト）
            - warnings: 警告情報のリスト
        """
        warnings = []

        # 全体順位を計算
        overall_standings = self.calculate_overall_standings(tournament_id)

        # 決勝T進出チーム（各グループ1位）
        knockout_teams = [s for s in overall_standings if s.rank == 1]

        # 残りのチーム（2位以下）
        remaining_teams = [s for s in overall_standings if s.rank > 1]

        # 同成績チームの検出（警告用）
        self._detect_same_stats_warnings(remaining_teams, warnings)

        # 4つの順位リーグに振り分け
        position_leagues = self._distribute_to_leagues(remaining_teams, 4)

        # チーム数が不均等な場合の警告
        league_sizes = [len(league) for league in position_leagues]
        if len(set(league_sizes)) > 1:
            warnings.append({
                'type': 'uneven',
                'message': 'チーム数が均等でないため、リーグによって試合数が異なります',
                'details': {f'league{i+1}': size for i, size in enumerate(league_sizes)},
            })

        return knockout_teams, position_leagues, warnings

    def _detect_same_stats_warnings(self, standings: List[Standing], warnings: List[Dict]):
        """同成績チームを検出して警告を追加"""
        # 同じ成績のチームをグループ化
        stats_groups = {}
        for s in standings:
            key = (s.rank, s.points, s.goal_difference, s.goals_for)
            if key not in stats_groups:
                stats_groups[key] = []
            stats_groups[key].append(s)

        # 同成績が複数あるグループを警告
        for key, group in stats_groups.items():
            if len(group) > 1:
                team_names = [s.team.name if s.team else f"Team#{s.team_id}" for s in group]
                warnings.append({
                    'type': 'random',
                    'message': f'同成績のチームがランダムで順位決定されました',
                    'details': team_names,
                })

    def _distribute_to_leagues(self, teams: List[Standing], league_count: int = 4) -> List[List[Standing]]:
        """
        チームを順位リーグに振り分け

        上位リーグから順に配分し、端数は上位リーグに多めに配分
        """
        leagues = [[] for _ in range(league_count)]

        if not teams:
            return leagues

        # 各リーグの基本サイズ
        base_size = len(teams) // league_count
        extra = len(teams) % league_count

        current_idx = 0
        for i in range(league_count):
            # 上位リーグに端数を配分
            size = base_size + (1 if i < extra else 0)
            leagues[i] = teams[current_idx:current_idx + size]
            current_idx += size

        return leagues
