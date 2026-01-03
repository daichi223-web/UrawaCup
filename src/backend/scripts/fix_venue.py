"""決勝会場を設定するスクリプト"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from models.venue import Venue

db = SessionLocal()

# 駒場スタジアムを決勝会場に設定
venue = db.query(Venue).filter(Venue.name.like('%駒場%')).first()
if venue:
    venue.is_finals_venue = True
    venue.for_final_day = True
    venue.group_id = None  # 決勝会場はグループなし
    db.commit()
    print(f"決勝会場を設定しました: {venue.name}")
    print(f"  is_finals_venue: {venue.is_finals_venue}")
    print(f"  for_final_day: {venue.for_final_day}")
    print(f"  group_id: {venue.group_id}")
else:
    # 駒場スタジアムがなければ新規作成
    from models.tournament import Tournament
    tournament = db.query(Tournament).first()
    if tournament:
        new_venue = Venue(
            tournament_id=tournament.id,
            name="駒場スタジアム",
            is_finals_venue=True,
            for_final_day=True,
            for_preliminary=False,
            group_id=None,
            max_matches_per_day=4,
            notes="決勝トーナメント会場"
        )
        db.add(new_venue)
        db.commit()
        print(f"新規決勝会場を作成しました: {new_venue.name}")

db.close()
