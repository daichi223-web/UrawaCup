"""
全試合にスコアと得点を追加するスクリプト
"""
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal, init_db
from models.team import Team
from models.player import Player
from models.match import Match, MatchStatus
from models.goal import Goal

def add_scores_and_goals(db):
    """全試合にスコアと得点を追加"""
    matches = db.query(Match).all()

    goal_count = 0
    matches_updated = 0

    for match in matches:
        # スコアが設定されていない試合にスコアを追加
        if match.home_score_total is None:
            match.home_score_half1 = random.randint(0, 3)
            match.home_score_half2 = random.randint(0, 3)
            match.home_score_total = match.home_score_half1 + match.home_score_half2
            match.away_score_half1 = random.randint(0, 3)
            match.away_score_half2 = random.randint(0, 3)
            match.away_score_total = match.away_score_half1 + match.away_score_half2
            match.status = MatchStatus.COMPLETED
            match.determine_result()
            matches_updated += 1

            # ゴールも追加
            home_players = db.query(Player).filter(
                Player.team_id == match.home_team_id,
                Player.is_active == True
            ).all()

            away_players = db.query(Player).filter(
                Player.team_id == match.away_team_id,
                Player.is_active == True
            ).all()

            # ホーム前半
            for _ in range(match.home_score_half1):
                if home_players:
                    scorer = random.choice(home_players)
                    goal = Goal(
                        match_id=match.id,
                        team_id=match.home_team_id,
                        player_id=scorer.id,
                        player_name=scorer.name,
                        minute=random.randint(1, 25),
                        half=1
                    )
                    db.add(goal)
                    goal_count += 1

            # ホーム後半
            for _ in range(match.home_score_half2):
                if home_players:
                    scorer = random.choice(home_players)
                    goal = Goal(
                        match_id=match.id,
                        team_id=match.home_team_id,
                        player_id=scorer.id,
                        player_name=scorer.name,
                        minute=random.randint(1, 25),
                        half=2
                    )
                    db.add(goal)
                    goal_count += 1

            # アウェイ前半
            for _ in range(match.away_score_half1):
                if away_players:
                    scorer = random.choice(away_players)
                    goal = Goal(
                        match_id=match.id,
                        team_id=match.away_team_id,
                        player_id=scorer.id,
                        player_name=scorer.name,
                        minute=random.randint(1, 25),
                        half=1
                    )
                    db.add(goal)
                    goal_count += 1

            # アウェイ後半
            for _ in range(match.away_score_half2):
                if away_players:
                    scorer = random.choice(away_players)
                    goal = Goal(
                        match_id=match.id,
                        team_id=match.away_team_id,
                        player_id=scorer.id,
                        player_name=scorer.name,
                        minute=random.randint(1, 25),
                        half=2
                    )
                    db.add(goal)
                    goal_count += 1

    db.flush()
    return matches_updated, goal_count


def main():
    print("=" * 50)
    print("全試合スコア・得点投入")
    print("=" * 50)

    init_db()
    db = SessionLocal()

    try:
        matches_updated, goal_count = add_scores_and_goals(db)
        db.commit()
        print(f"\n試合更新: {matches_updated}件")
        print(f"得点追加: {goal_count}件")
        print("\n完了しました！")

    except Exception as e:
        db.rollback()
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
