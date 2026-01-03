"""
ダミーデータ投入スクリプト
浦和カップ トーナメント管理システム
"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from database import SessionLocal, init_db
from models.tournament import Tournament
from models.team import Team, TeamType
from models.venue import Venue
from models.group import Group

# 大会設定
TOURNAMENT_CONFIG = {
    "name": "浦和カップ 2026",
    "edition": 45,
    "year": 2026,
    "start_date": date(2026, 3, 21),
    "end_date": date(2026, 3, 23),
    "match_duration": 50,
    "half_duration": 25,
    "interval_minutes": 15,
}

# チームリスト（4グループ x 6チーム = 24チーム）
TEAMS = {
    "A": [
        {"name": "浦和レッズユース", "short_name": "浦和", "team_type": TeamType.LOCAL, "is_venue_host": True, "prefecture": "埼玉県"},
        {"name": "大宮アルディージャU18", "short_name": "大宮", "team_type": TeamType.LOCAL, "is_venue_host": False, "prefecture": "埼玉県"},
        {"name": "前橋育英高校", "short_name": "前橋育英", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "群馬県"},
        {"name": "市立船橋高校", "short_name": "市船", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "千葉県"},
        {"name": "青森山田高校", "short_name": "青森山田", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "青森県"},
        {"name": "流経大柏高校", "short_name": "流経柏", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "千葉県"},
    ],
    "B": [
        {"name": "浦和南高校", "short_name": "浦和南", "team_type": TeamType.LOCAL, "is_venue_host": True, "prefecture": "埼玉県"},
        {"name": "武南高校", "short_name": "武南", "team_type": TeamType.LOCAL, "is_venue_host": False, "prefecture": "埼玉県"},
        {"name": "静岡学園高校", "short_name": "静学", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "静岡県"},
        {"name": "東福岡高校", "short_name": "東福岡", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "福岡県"},
        {"name": "桐生第一高校", "short_name": "桐一", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "群馬県"},
        {"name": "帝京高校", "short_name": "帝京", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "東京都"},
    ],
    "C": [
        {"name": "浦和西高校", "short_name": "浦和西", "team_type": TeamType.LOCAL, "is_venue_host": True, "prefecture": "埼玉県"},
        {"name": "浦和東高校", "short_name": "浦和東", "team_type": TeamType.LOCAL, "is_venue_host": False, "prefecture": "埼玉県"},
        {"name": "国見高校", "short_name": "国見", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "長崎県"},
        {"name": "鹿島アントラーズユース", "short_name": "鹿島", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "茨城県"},
        {"name": "清水エスパルスユース", "short_name": "清水", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "静岡県"},
        {"name": "横浜F・マリノスユース", "short_name": "横浜FM", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "神奈川県"},
    ],
    "D": [
        {"name": "市立浦和高校", "short_name": "市浦和", "team_type": TeamType.LOCAL, "is_venue_host": True, "prefecture": "埼玉県"},
        {"name": "埼玉栄高校", "short_name": "埼玉栄", "team_type": TeamType.LOCAL, "is_venue_host": False, "prefecture": "埼玉県"},
        {"name": "名古屋グランパスU18", "short_name": "名古屋", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "愛知県"},
        {"name": "ガンバ大阪ユース", "short_name": "G大阪", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "大阪府"},
        {"name": "セレッソ大阪U18", "short_name": "C大阪", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "大阪府"},
        {"name": "FC東京U18", "short_name": "FC東京", "team_type": TeamType.INVITED, "is_venue_host": False, "prefecture": "東京都"},
    ],
}

# 会場リスト（各グループに1会場を割り当て）
VENUES = [
    {"name": "駒場スタジアム", "address": "さいたま市浦和区駒場", "for_final_day": True, "for_preliminary": False},
    {"name": "浦和駒場サブグラウンド", "address": "さいたま市浦和区駒場", "group_id": "A"},
    {"name": "浦和南高校グラウンド", "address": "さいたま市南区", "group_id": "B"},
    {"name": "レッズランド", "address": "さいたま市桜区", "group_id": "C"},
    {"name": "市立浦和高校グラウンド", "address": "さいたま市浦和区", "group_id": "D"},
]


def seed_data():
    """ダミーデータを投入"""
    db = SessionLocal()

    try:
        # 既存データの確認
        existing = db.query(Tournament).filter(Tournament.year == 2026).first()
        if existing:
            print(f"大会 '{existing.name}' (ID: {existing.id}) を使用します")
            tournament = existing
            # 既存のチームがあるか確認
            existing_teams = db.query(Team).filter(Team.tournament_id == tournament.id).count()
            if existing_teams > 0:
                print(f"既に{existing_teams}チームが登録されています。スキップします。")
                return tournament.id
        else:
            # 大会作成
            tournament = Tournament(**TOURNAMENT_CONFIG)
            db.add(tournament)
            db.flush()
            print(f"大会作成: {tournament.name} (ID: {tournament.id})")

        # 会場作成
        for venue_data in VENUES:
            venue = Venue(tournament_id=tournament.id, **venue_data)
            db.add(venue)
        print(f"会場作成: {len(VENUES)}件")

        # グループ作成
        groups = {}
        for group_id in ["A", "B", "C", "D"]:
            # 既存グループがあるか確認
            existing_group = db.query(Group).filter(
                Group.id == group_id,
                Group.tournament_id == tournament.id
            ).first()
            if existing_group:
                groups[group_id] = existing_group
            else:
                group = Group(
                    id=group_id,
                    tournament_id=tournament.id,
                    name=f"Group {group_id}"
                )
                db.add(group)
                groups[group_id] = group
        db.flush()
        print(f"グループ作成: 4件")

        # チーム作成
        team_count = 0
        for group_id, team_list in TEAMS.items():
            for order, team_data in enumerate(team_list, 1):
                team = Team(
                    tournament_id=tournament.id,
                    group_id=group_id,
                    group_order=order,
                    **team_data
                )
                db.add(team)
                team_count += 1
        print(f"チーム作成: {team_count}件")

        db.commit()
        print("\nダミーデータの投入が完了しました！")
        print(f"Tournament ID: {tournament.id}")
        return tournament.id

    except Exception as e:
        db.rollback()
        print(f"エラー: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("浦和カップ ダミーデータ投入")
    print("=" * 50)
    init_db()
    seed_data()
