"""
対戦除外ペアを設定するスクリプト
6チーム総当たり15試合 → 3ペア除外 → 12試合（各チーム4試合）
"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from models.team import Team
from models.exclusion_pair import ExclusionPair


def get_team_by_name(db, tournament_id: int, short_name: str) -> Team:
    """短縮名でチームを取得"""
    team = db.query(Team).filter(
        Team.tournament_id == tournament_id,
        Team.short_name == short_name
    ).first()
    if not team:
        raise ValueError(f"Team not found: {short_name}")
    return team


def setup_exclusion_pairs():
    """対戦除外ペアを設定"""
    db = SessionLocal()
    tournament_id = 1

    try:
        # 既存の除外ペアを削除
        db.query(ExclusionPair).filter(
            ExclusionPair.tournament_id == tournament_id
        ).delete()
        print("既存の除外ペアを削除しました")

        # 除外ペア定義（グループID, チーム1短縮名, チーム2短縮名, 理由）
        # 各グループ3ペア = 12ペア
        exclusion_definitions = [
            # グループA: 浦和、大宮、前橋育英、市船、青森山田、流経柏
            ("A", "浦和", "大宮", "埼玉県地元校同士"),
            ("A", "市船", "流経柏", "千葉県同士"),
            ("A", "前橋育英", "青森山田", "強豪校調整"),

            # グループB: 浦和南、武南、静学、東福岡、桐一、帝京
            ("B", "浦和南", "武南", "埼玉県地元校同士"),
            ("B", "静学", "桐一", "地域調整"),
            ("B", "東福岡", "帝京", "強豪校調整"),

            # グループC: 浦和西、浦和東、国見、鹿島、清水、横浜FM
            ("C", "浦和西", "浦和東", "浦和地区地元校同士"),
            ("C", "清水", "横浜FM", "静岡・神奈川近県"),
            ("C", "国見", "鹿島", "強豪校調整"),

            # グループD: 市浦和、埼玉栄、名古屋、G大阪、C大阪、FC東京
            ("D", "市浦和", "埼玉栄", "埼玉県地元校同士"),
            ("D", "G大阪", "C大阪", "大阪府同士"),
            ("D", "名古屋", "FC東京", "強豪校調整"),
        ]

        created_count = 0
        for group_id, team1_name, team2_name, reason in exclusion_definitions:
            team1 = get_team_by_name(db, tournament_id, team1_name)
            team2 = get_team_by_name(db, tournament_id, team2_name)

            exclusion = ExclusionPair(
                tournament_id=tournament_id,
                group_id=group_id,
                team1_id=team1.id,
                team2_id=team2.id,
                reason=reason
            )
            db.add(exclusion)
            created_count += 1
            print(f"  除外: グループ{group_id} - {team1_name} vs {team2_name} ({reason})")

        db.commit()
        print(f"\n{created_count}件の除外ペアを設定しました")

        # 確認: 各グループの除外数
        print("\nグループ別除外ペア数:")
        for group_id in ["A", "B", "C", "D"]:
            count = db.query(ExclusionPair).filter(
                ExclusionPair.tournament_id == tournament_id,
                ExclusionPair.group_id == group_id
            ).count()
            print(f"  グループ{group_id}: {count}ペア")

    except Exception as e:
        db.rollback()
        print(f"エラー: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("対戦除外ペア設定")
    print("=" * 50)
    setup_exclusion_pairs()
