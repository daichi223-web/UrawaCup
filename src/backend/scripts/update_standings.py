"""順位表を強制更新するスクリプト"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from models.match import Match, MatchStage
from models.tournament import Tournament
from services.standing_service import StandingService

db = SessionLocal()

print("=" * 60)
print("順位表更新")
print("=" * 60)

# 試合のステージを確認
print("\n[1] 試合ステージ確認:")
matches = db.query(Match).limit(10).all()
for m in matches:
    print(f"  ID:{m.id} stage={m.stage} group={m.group_id} status={m.status}")

# ステージがNoneの試合をPRELIMINARYに設定
updated = 0
for m in db.query(Match).filter(Match.stage == None).all():
    if m.group_id:
        m.stage = MatchStage.PRELIMINARY
        updated += 1

if updated > 0:
    db.commit()
    print(f"\n{updated}件の試合のステージをPRELIMINARYに設定しました")

# 全グループの順位表を更新
print("\n[2] 順位表更新:")
tournament = db.query(Tournament).first()
if tournament:
    standing_service = StandingService(db)
    for group_id in ["A", "B", "C", "D"]:
        try:
            standings = standing_service.update_group_standings(tournament.id, group_id)
            print(f"  グループ{group_id}: {len(standings)}チーム更新")
        except Exception as e:
            print(f"  グループ{group_id}: エラー - {e}")
else:
    print("  大会が見つかりません")

print("\n完了しました！")
db.close()
