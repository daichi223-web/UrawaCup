"""データ確認スクリプト"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from models.team import Team
from models.player import Player
from models.match import Match
from models.goal import Goal

db = SessionLocal()

print("=" * 50)
print("データ確認")
print("=" * 50)

# チーム数
team_count = db.query(Team).count()
print(f"\nチーム数: {team_count}")

# 選手数
player_count = db.query(Player).count()
print(f"選手数: {player_count}")

# 試合数とスコア状況
match_count = db.query(Match).count()
matches_with_score = db.query(Match).filter(Match.home_score_total != None).count()
matches_with_zero = db.query(Match).filter(Match.home_score_total == 0, Match.away_score_total == 0).count()
print(f"\n試合数: {match_count}")
print(f"  スコアあり: {matches_with_score}")
print(f"  0-0の試合: {matches_with_zero}")

# 得点数
goal_count = db.query(Goal).count()
print(f"\n得点数: {goal_count}")

# サンプル試合表示
print("\n試合サンプル（最初の5件）:")
matches = db.query(Match).limit(5).all()
for m in matches:
    ht = db.query(Team).filter(Team.id == m.home_team_id).first()
    at = db.query(Team).filter(Team.id == m.away_team_id).first()
    home_name = ht.short_name if ht else "?"
    away_name = at.short_name if at else "?"
    print(f"  {m.id}: {home_name} {m.home_score_total}-{m.away_score_total} {away_name}")

    # この試合のゴール
    goals = db.query(Goal).filter(Goal.match_id == m.id).all()
    for g in goals:
        half = "前半" if g.half == 1 else "後半"
        print(f"      {half}{g.minute}分 {g.player_name}")

db.close()
