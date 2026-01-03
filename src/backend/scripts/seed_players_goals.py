"""
選手と得点のダミーデータ投入スクリプト
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

# 日本人選手の名前サンプル（サッカー選手風）
FIRST_NAMES = [
    "翔太", "大輝", "拓海", "蒼", "陸", "颯太", "悠斗", "蓮", "湊", "陽太",
    "大翔", "悠真", "樹", "奏太", "健太", "優斗", "隼人", "駿", "航", "涼太",
    "大和", "蒼汰", "颯", "遼", "海斗", "翼", "拓真", "陽", "凱斗", "匠",
    "唯心", "蒼大", "洸", "晴", "大地", "勇輝", "康太", "裕太", "将太", "雄大"
]

LAST_NAMES = [
    "田中", "鈴木", "佐藤", "山本", "渡辺", "高橋", "中村", "小林", "伊藤", "斎藤",
    "加藤", "吉田", "山田", "佐々木", "松本", "井上", "木村", "林", "清水", "山口",
    "平井", "辻本", "中島", "前田", "石川", "藤田", "岡田", "後藤", "村上", "近藤",
    "森", "新井", "藤井", "池田", "橋本", "福田", "坂本", "横山", "阿部", "遠藤"
]

POSITIONS = ["GK", "DF", "DF", "DF", "DF", "MF", "MF", "MF", "MF", "FW", "FW"]


def generate_player_name():
    """ランダムな選手名を生成"""
    return f"{random.choice(LAST_NAMES)}{random.choice(FIRST_NAMES)}"


def seed_players(db):
    """各チームに選手を追加"""
    teams = db.query(Team).all()
    player_count = 0

    for team in teams:
        # 既存の選手確認
        existing = db.query(Player).filter(Player.team_id == team.id).count()
        if existing > 0:
            print(f"  {team.name}: 既に{existing}名の選手が登録済み")
            continue

        # 25名の選手を生成
        for i in range(1, 26):
            pos_index = min(i - 1, len(POSITIONS) - 1)
            player = Player(
                team_id=team.id,
                number=i,
                name=generate_player_name(),
                grade=random.choice([1, 2, 3]),
                position=POSITIONS[pos_index] if i <= 11 else random.choice(POSITIONS),
                is_captain=(i == 10),
                is_active=True
            )
            db.add(player)
            player_count += 1

    db.flush()
    print(f"選手作成: {player_count}名")
    return player_count


def seed_goals(db):
    """試合に得点を追加"""
    # 完了した試合を取得
    matches = db.query(Match).filter(Match.status == MatchStatus.COMPLETED).all()

    if not matches:
        # スケジュール済みの試合も取得してスコアを設定
        matches = db.query(Match).all()

    goal_count = 0
    matches_updated = 0

    for match in matches:
        # 既存のゴール確認
        existing_goals = db.query(Goal).filter(Goal.match_id == match.id).count()
        if existing_goals > 0:
            continue

        # スコアが設定されていない場合は設定
        if match.home_score_total is None:
            match.home_score_half1 = random.randint(0, 2)
            match.home_score_half2 = random.randint(0, 2)
            match.home_score_total = match.home_score_half1 + match.home_score_half2
            match.away_score_half1 = random.randint(0, 2)
            match.away_score_half2 = random.randint(0, 2)
            match.away_score_total = match.away_score_half1 + match.away_score_half2
            match.status = MatchStatus.COMPLETED
            match.determine_result()
            matches_updated += 1

        # ホームチームの選手を取得
        home_players = db.query(Player).filter(
            Player.team_id == match.home_team_id,
            Player.is_active == True
        ).all()

        # アウェイチームの選手を取得
        away_players = db.query(Player).filter(
            Player.team_id == match.away_team_id,
            Player.is_active == True
        ).all()

        # ホームチームの得点を追加
        for _ in range(match.home_score_half1 or 0):
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

        for _ in range(match.home_score_half2 or 0):
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

        # アウェイチームの得点を追加
        for _ in range(match.away_score_half1 or 0):
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

        for _ in range(match.away_score_half2 or 0):
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
    print(f"試合更新: {matches_updated}件")
    print(f"得点作成: {goal_count}件")
    return goal_count


def main():
    print("=" * 50)
    print("選手・得点 ダミーデータ投入")
    print("=" * 50)

    init_db()
    db = SessionLocal()

    try:
        print("\n[1] 選手データ投入...")
        seed_players(db)

        print("\n[2] 得点データ投入...")
        seed_goals(db)

        db.commit()
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
