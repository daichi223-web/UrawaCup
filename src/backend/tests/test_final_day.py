"""
最終日組み合わせ機能のテスト

swap-teams API、generate-finals、generate-training のテスト
"""

import os
import pytest
from datetime import date, time
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.tournament import Tournament
from models.team import Team, TeamType
from models.venue import Venue
from models.match import Match, MatchStage, MatchStatus
from models.user import User, UserRole
from models.group import Group
from models.standing import Standing
from utils.auth import hash_password, create_access_token


def create_test_user(session: Session, role: UserRole = UserRole.ADMIN) -> User:
    """テスト用ユーザーを作成"""
    user = User(
        username=f"testuser_{role.value}",
        display_name="Test Admin",
        role=role,
        password_hash=hash_password("testpassword123"),
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_test_tournament(session: Session) -> Tournament:
    """テスト用大会を作成"""
    tournament = Tournament(
        name="テスト大会",
        edition=1,
        year=2024,
        start_date=date(2024, 3, 25),
        end_date=date(2024, 3, 27),
        match_duration=50,
        half_duration=25,
        interval_minutes=15,
    )
    session.add(tournament)
    session.commit()
    session.refresh(tournament)
    return tournament


def create_test_venue(session: Session, tournament_id: int, is_finals: bool = False) -> Venue:
    """テスト用会場を作成"""
    venue = Venue(
        tournament_id=tournament_id,
        name="テスト会場" if not is_finals else "駒場スタジアム",
        address="さいたま市",
        max_matches_per_day=6,
        for_preliminary=not is_finals,
        for_final_day=is_finals,
        is_finals_venue=is_finals,
    )
    session.add(venue)
    session.commit()
    session.refresh(venue)
    return venue


def create_test_teams(session: Session, tournament_id: int, count: int = 4) -> list[Team]:
    """テスト用チームを作成"""
    teams = []
    for i in range(count):
        team = Team(
            tournament_id=tournament_id,
            name=f"テストチーム{i+1}",
            short_name=f"T{i+1}",
            team_type=TeamType.LOCAL,
            group_id=["A", "B", "C", "D"][i % 4],
            group_order=1,
        )
        session.add(team)
        teams.append(team)
    session.commit()
    for team in teams:
        session.refresh(team)
    return teams


def create_test_matches(
    session: Session,
    tournament_id: int,
    venue_id: int,
    teams: list[Team],
    stage: MatchStage = MatchStage.TRAINING
) -> list[Match]:
    """テスト用試合を作成"""
    matches = []
    for i in range(0, len(teams) - 1, 2):
        match = Match(
            tournament_id=tournament_id,
            venue_id=venue_id,
            home_team_id=teams[i].id,
            away_team_id=teams[i + 1].id,
            match_date=date(2024, 3, 27),
            match_time=time(9, 0),
            match_order=i // 2 + 1,
            stage=stage,
            status=MatchStatus.SCHEDULED,
        )
        session.add(match)
        matches.append(match)
    session.commit()
    for match in matches:
        session.refresh(match)
    return matches


def get_auth_headers(user: User) -> dict:
    """認証ヘッダーを取得"""
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestSwapTeamsAPI:
    """swap-teams APIのテスト"""

    def test_swap_teams_success(self, client: TestClient, test_session: Session):
        """正常系: チーム入れ替えが成功する"""
        # セットアップ
        user = create_test_user(test_session)
        tournament = create_test_tournament(test_session)
        venue = create_test_venue(test_session, tournament.id, is_finals=True)
        teams = create_test_teams(test_session, tournament.id, 4)
        matches = create_test_matches(test_session, tournament.id, venue.id, teams)

        # 元のチーム配置を確認
        match1_home_original = matches[0].home_team_id
        match2_home_original = matches[1].home_team_id

        # チーム入れ替えリクエスト（認証ヘッダー付き）
        response = client.post(
            "/api/matches/swap-teams",
            json={
                "match1Id": matches[0].id,
                "side1": "home",
                "match2Id": matches[1].id,
                "side2": "home",
            },
            headers=get_auth_headers(user),
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "チームを入れ替えました"

        # DBを再読み込みして確認
        test_session.refresh(matches[0])
        test_session.refresh(matches[1])
        assert matches[0].home_team_id == match2_home_original
        assert matches[1].home_team_id == match1_home_original

    def test_swap_teams_completed_match_rejected(
        self, client: TestClient, test_session: Session
    ):
        """異常系: 完了済み試合の入れ替えは拒否される"""
        user = create_test_user(test_session)
        tournament = create_test_tournament(test_session)
        venue = create_test_venue(test_session, tournament.id, is_finals=True)
        teams = create_test_teams(test_session, tournament.id, 4)
        matches = create_test_matches(test_session, tournament.id, venue.id, teams)

        # 試合1を完了済みに変更
        matches[0].status = MatchStatus.COMPLETED
        test_session.commit()

        # チーム入れ替えリクエスト
        response = client.post(
            "/api/matches/swap-teams",
            json={
                "match1Id": matches[0].id,
                "side1": "home",
                "match2Id": matches[1].id,
                "side2": "home",
            },
            headers=get_auth_headers(user),
        )

        # 検証
        assert response.status_code == 400
        assert "完了しています" in response.json()["detail"]

    def test_swap_teams_locked_match_rejected(
        self, client: TestClient, test_session: Session
    ):
        """異常系: ロック中の試合の入れ替えは拒否される"""
        user = create_test_user(test_session)
        tournament = create_test_tournament(test_session)
        venue = create_test_venue(test_session, tournament.id, is_finals=True)
        teams = create_test_teams(test_session, tournament.id, 4)
        matches = create_test_matches(test_session, tournament.id, venue.id, teams)

        # 試合1をロック
        matches[0].is_locked = True
        matches[0].locked_by = user.id
        test_session.commit()

        # チーム入れ替えリクエスト
        response = client.post(
            "/api/matches/swap-teams",
            json={
                "match1Id": matches[0].id,
                "side1": "home",
                "match2Id": matches[1].id,
                "side2": "home",
            },
            headers=get_auth_headers(user),
        )

        # 検証
        assert response.status_code == 423
        assert "編集中" in response.json()["detail"]

    def test_swap_teams_same_team_rejected(
        self, client: TestClient, test_session: Session
    ):
        """異常系: 同じチーム同士の入れ替えは拒否される"""
        user = create_test_user(test_session)
        tournament = create_test_tournament(test_session)
        venue = create_test_venue(test_session, tournament.id, is_finals=True)
        teams = create_test_teams(test_session, tournament.id, 4)
        matches = create_test_matches(test_session, tournament.id, venue.id, teams)

        # 同じ試合の同じサイドを入れ替え（実質同じチーム）
        response = client.post(
            "/api/matches/swap-teams",
            json={
                "match1Id": matches[0].id,
                "side1": "home",
                "match2Id": matches[0].id,
                "side2": "home",
            },
            headers=get_auth_headers(user),
        )

        # 検証
        assert response.status_code == 400

    def test_swap_teams_unauthorized(self, client: TestClient, test_session: Session):
        """異常系: 未認証ユーザーはアクセスできない"""
        tournament = create_test_tournament(test_session)
        venue = create_test_venue(test_session, tournament.id, is_finals=True)
        teams = create_test_teams(test_session, tournament.id, 4)
        matches = create_test_matches(test_session, tournament.id, venue.id, teams)

        # 認証なしでリクエスト
        response = client.post(
            "/api/matches/swap-teams",
            json={
                "match1Id": matches[0].id,
                "side1": "home",
                "match2Id": matches[1].id,
                "side2": "home",
            }
        )

        # 検証
        assert response.status_code in [401, 403]


class TestGenerateFinalsAPI:
    """決勝トーナメント生成APIのテスト"""

    def test_generate_finals_requires_standings(
        self, client: TestClient, test_session: Session
    ):
        """異常系: 順位表がない場合は生成できない"""
        user = create_test_user(test_session)
        tournament = create_test_tournament(test_session)
        venue = create_test_venue(test_session, tournament.id, is_finals=True)

        # 決勝生成リクエスト
        response = client.post(
            f"/api/matches/generate-finals/{tournament.id}",
            params={
                "match_date": "2024-03-27",
                "start_time": "09:00:00",
            },
            headers=get_auth_headers(user),
        )

        # 順位表がないためエラー
        assert response.status_code == 400


class TestUpdateFinalMatchTeamsAPI:
    """決勝試合チーム更新APIのテスト"""

    def test_update_final_match_teams_success(
        self, client: TestClient, test_session: Session
    ):
        """正常系: 決勝試合のチームを更新できる"""
        user = create_test_user(test_session)
        tournament = create_test_tournament(test_session)
        venue = create_test_venue(test_session, tournament.id, is_finals=True)
        teams = create_test_teams(test_session, tournament.id, 4)

        # 準決勝試合を作成
        match = Match(
            tournament_id=tournament.id,
            venue_id=venue.id,
            home_team_id=teams[0].id,
            away_team_id=teams[1].id,
            match_date=date(2024, 3, 27),
            match_time=time(9, 0),
            match_order=1,
            stage=MatchStage.SEMIFINAL,
            status=MatchStatus.SCHEDULED,
        )
        test_session.add(match)
        test_session.commit()
        test_session.refresh(match)

        # チーム更新リクエスト
        response = client.put(
            f"/api/matches/finals/{match.id}/teams",
            params={
                "home_team_id": teams[2].id,
                "away_team_id": teams[3].id,
            },
            headers=get_auth_headers(user),
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["home_team_id"] == teams[2].id
        assert data["away_team_id"] == teams[3].id

    def test_update_final_match_teams_non_final_rejected(
        self, client: TestClient, test_session: Session
    ):
        """異常系: 予選試合のチームは更新できない"""
        user = create_test_user(test_session)
        tournament = create_test_tournament(test_session)
        venue = create_test_venue(test_session, tournament.id)
        teams = create_test_teams(test_session, tournament.id, 4)

        # 予選試合を作成
        match = Match(
            tournament_id=tournament.id,
            venue_id=venue.id,
            home_team_id=teams[0].id,
            away_team_id=teams[1].id,
            match_date=date(2024, 3, 25),
            match_time=time(9, 0),
            match_order=1,
            stage=MatchStage.PRELIMINARY,
            status=MatchStatus.SCHEDULED,
        )
        test_session.add(match)
        test_session.commit()
        test_session.refresh(match)

        # チーム更新リクエスト
        response = client.put(
            f"/api/matches/finals/{match.id}/teams",
            params={
                "home_team_id": teams[2].id,
                "away_team_id": teams[3].id,
            },
            headers=get_auth_headers(user),
        )

        # 検証
        assert response.status_code == 400
        assert "決勝トーナメント" in response.json()["detail"]
