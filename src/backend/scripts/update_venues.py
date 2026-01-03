"""
会場にグループIDを割り当てるスクリプト
"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from models.venue import Venue

# 会場とグループの対応
VENUE_GROUP_MAPPING = {
    "浦和駒場サブグラウンド": "A",
    "浦和南高校グラウンド": "B",
    "レッズランド": "C",
}

# 追加する会場
NEW_VENUES = [
    {"name": "市立浦和高校グラウンド", "address": "さいたま市浦和区", "group_id": "D", "tournament_id": 1},
]


def update_venues():
    """会場にグループIDを割り当て"""
    db = SessionLocal()

    try:
        # 既存の会場にグループIDを割り当て
        for venue_name, group_id in VENUE_GROUP_MAPPING.items():
            venue = db.query(Venue).filter(Venue.name == venue_name).first()
            if venue:
                venue.group_id = group_id
                print(f"更新: {venue_name} -> グループ {group_id}")
            else:
                print(f"会場が見つかりません: {venue_name}")

        # 新しい会場を追加
        for venue_data in NEW_VENUES:
            existing = db.query(Venue).filter(Venue.name == venue_data["name"]).first()
            if not existing:
                venue = Venue(**venue_data)
                db.add(venue)
                print(f"作成: {venue_data['name']} -> グループ {venue_data['group_id']}")
            else:
                existing.group_id = venue_data["group_id"]
                print(f"更新: {venue_data['name']} -> グループ {venue_data['group_id']}")

        db.commit()
        print("\n会場の更新が完了しました！")

        # 確認表示
        print("\n会場一覧:")
        venues = db.query(Venue).all()
        for v in venues:
            print(f"  - {v.name}: グループ {v.group_id or '(なし)'}")

    except Exception as e:
        db.rollback()
        print(f"エラー: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("会場グループID更新")
    print("=" * 50)
    update_venues()
