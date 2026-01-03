"""問題確認スクリプト"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from models.venue import Venue
from models.match import Match, MatchStatus
from models.standing import Standing
from models.team import Team

db = SessionLocal()

print("=" * 60)
print("問題確認")
print("=" * 60)

# 1. 会場確認
print("\n[1] 会場一覧:")
venues = db.query(Venue).all()
for v in venues:
    finals_flag = "★決勝会場" if v.is_finals_venue else ""
    final_day = "(最終日)" if v.for_final_day else ""
    group = f"(グループ{v.group_id})" if v.group_id else "(グループなし)"
    print(f"  {v.id}: {v.name} {group} {final_day} {finals_flag}")

# 決勝会場があるか確認
finals_venue = db.query(Venue).filter(Venue.is_finals_venue == True).first()
if not finals_venue:
    # 代替会場を確認
    alt_venue = db.query(Venue).filter(
        Venue.for_final_day == True,
        Venue.group_id == None
    ).first()
    if alt_venue:
        print(f"\n  ⚠ is_finals_venue=Trueの会場がありませんが、代替会場あり: {alt_venue.name}")
    else:
        print("\n  ❌ 決勝会場がありません。is_finals_venue=Trueの会場を設定してください。")
else:
    print(f"\n  ✓ 決勝会場: {finals_venue.name}")

# 2. 試合結果と順位表
print("\n[2] 試合状況:")
total_matches = db.query(Match).count()
completed = db.query(Match).filter(Match.status == MatchStatus.COMPLETED).count()
print(f"  総試合数: {total_matches}")
print(f"  完了: {completed}")

# 3. 順位表確認
print("\n[3] 順位表:")
standings = db.query(Standing).all()
if not standings:
    print("  ❌ 順位表データがありません。")
else:
    print(f"  登録数: {len(standings)}")
    for s in standings[:5]:
        team = db.query(Team).filter(Team.id == s.team_id).first()
        team_name = team.short_name if team else "?"
        print(f"    グループ{s.group_id} {s.rank}位: {team_name} ({s.played}試合 {s.won}勝{s.drawn}分{s.lost}敗)")

# 4. 決勝トーナメント試合
print("\n[4] 決勝トーナメント試合:")
finals_matches = db.query(Match).filter(
    Match.stage.in_(['semifinal', 'third_place', 'final'])
).all()
if not finals_matches:
    print("  決勝トーナメント試合がありません。")
else:
    for m in finals_matches:
        ht = db.query(Team).filter(Team.id == m.home_team_id).first()
        at = db.query(Team).filter(Team.id == m.away_team_id).first()
        h_name = ht.short_name if ht else "未定"
        a_name = at.short_name if at else "未定"
        print(f"  {m.stage}: {h_name} vs {a_name} ({m.status})")

db.close()
