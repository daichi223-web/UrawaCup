#!/usr/bin/env python3
"""
グループテーブル複合主キーマイグレーションスクリプト

このスクリプトは既存のデータベースを複合主キー(tournament_id, id)に対応した
スキーマに変更します。

使用方法:
    python scripts/migrate_groups_composite_key.py

注意:
    - 実行前に必ずデータベースのバックアップを取得してください
    - SQLite専用のスクリプトです
"""

import os
import sys
import shutil
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def backup_database(db_path: str) -> str:
    """データベースファイルをバックアップ"""
    if not os.path.exists(db_path):
        print(f"データベースファイルが見つかりません: {db_path}")
        return None

    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"バックアップを作成しました: {backup_path}")
    return backup_path


def check_migration_needed(engine) -> bool:
    """マイグレーションが必要かどうかを確認"""
    with engine.connect() as conn:
        # groupsテーブルの主キー構成を確認
        result = conn.execute(text("PRAGMA table_info(groups)"))
        columns = {row[1]: row[5] for row in result}  # name: pk

        # tournament_idとidの両方が主キーかどうか確認
        if columns.get('tournament_id', 0) > 0 and columns.get('id', 0) > 0:
            print("マイグレーション済みです。")
            return False
        elif columns.get('id', 0) > 0 and columns.get('tournament_id', 0) == 0:
            print("マイグレーションが必要です。")
            return True
        else:
            print("テーブル構造が不明です。手動で確認してください。")
            return False


def run_migration(engine) -> bool:
    """マイグレーションを実行"""
    with engine.connect() as conn:
        try:
            # 外部キー制約を無効化
            conn.execute(text("PRAGMA foreign_keys=OFF;"))
            conn.commit()

            print("teams テーブルを再作成中...")
            conn.execute(text("""
                CREATE TABLE teams_new (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    tournament_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    short_name VARCHAR(50),
                    team_type VARCHAR(7) NOT NULL DEFAULT 'invited',
                    is_venue_host BOOLEAN NOT NULL DEFAULT 0,
                    group_id VARCHAR(1),
                    group_order INTEGER,
                    prefecture VARCHAR(20),
                    notes VARCHAR(500),
                    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                    updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                    FOREIGN KEY(tournament_id) REFERENCES tournaments (id) ON DELETE CASCADE,
                    FOREIGN KEY(tournament_id, group_id) REFERENCES groups (tournament_id, id) ON DELETE SET NULL
                )
            """))
            conn.execute(text("INSERT INTO teams_new SELECT * FROM teams"))
            conn.execute(text("DROP TABLE teams"))
            conn.execute(text("ALTER TABLE teams_new RENAME TO teams"))
            conn.commit()
            print("  完了")

            print("standings テーブルを再作成中...")
            conn.execute(text("""
                CREATE TABLE standings_new (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    tournament_id INTEGER NOT NULL,
                    group_id VARCHAR(1) NOT NULL,
                    team_id INTEGER NOT NULL,
                    rank INTEGER NOT NULL DEFAULT 0,
                    played INTEGER NOT NULL DEFAULT 0,
                    won INTEGER NOT NULL DEFAULT 0,
                    drawn INTEGER NOT NULL DEFAULT 0,
                    lost INTEGER NOT NULL DEFAULT 0,
                    goals_for INTEGER NOT NULL DEFAULT 0,
                    goals_against INTEGER NOT NULL DEFAULT 0,
                    goal_difference INTEGER NOT NULL DEFAULT 0,
                    points INTEGER NOT NULL DEFAULT 0,
                    rank_reason VARCHAR(100),
                    updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
                    FOREIGN KEY(tournament_id) REFERENCES tournaments (id) ON DELETE CASCADE,
                    FOREIGN KEY(team_id) REFERENCES teams (id) ON DELETE CASCADE,
                    FOREIGN KEY(tournament_id, group_id) REFERENCES groups (tournament_id, id) ON DELETE CASCADE
                )
            """))
            conn.execute(text("INSERT INTO standings_new SELECT * FROM standings"))
            conn.execute(text("DROP TABLE standings"))
            conn.execute(text("ALTER TABLE standings_new RENAME TO standings"))
            conn.commit()
            print("  完了")

            print("matches テーブルを再作成中...")
            conn.execute(text("""
                CREATE TABLE matches_new (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    tournament_id INTEGER NOT NULL,
                    group_id VARCHAR(1),
                    venue_id INTEGER NOT NULL,
                    home_team_id INTEGER NOT NULL,
                    away_team_id INTEGER NOT NULL,
                    match_date DATE NOT NULL,
                    match_time TIME NOT NULL,
                    match_order INTEGER NOT NULL,
                    stage VARCHAR(11) NOT NULL DEFAULT 'preliminary',
                    status VARCHAR(11) NOT NULL DEFAULT 'scheduled',
                    home_score_half1 INTEGER,
                    home_score_half2 INTEGER,
                    home_score_total INTEGER,
                    away_score_half1 INTEGER,
                    away_score_half2 INTEGER,
                    away_score_total INTEGER,
                    home_pk INTEGER,
                    away_pk INTEGER,
                    has_penalty_shootout BOOLEAN NOT NULL DEFAULT 0,
                    result VARCHAR(8),
                    is_locked BOOLEAN NOT NULL DEFAULT 0,
                    locked_by INTEGER,
                    locked_at DATETIME,
                    entered_by INTEGER,
                    entered_at DATETIME,
                    approval_status VARCHAR(8),
                    approved_by INTEGER,
                    approved_at DATETIME,
                    rejection_reason VARCHAR(500),
                    notes VARCHAR(500),
                    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                    updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                    FOREIGN KEY(tournament_id) REFERENCES tournaments (id) ON DELETE CASCADE,
                    FOREIGN KEY(venue_id) REFERENCES venues (id) ON DELETE RESTRICT,
                    FOREIGN KEY(home_team_id) REFERENCES teams (id) ON DELETE RESTRICT,
                    FOREIGN KEY(away_team_id) REFERENCES teams (id) ON DELETE RESTRICT,
                    FOREIGN KEY(locked_by) REFERENCES users (id) ON DELETE SET NULL,
                    FOREIGN KEY(entered_by) REFERENCES users (id) ON DELETE SET NULL,
                    FOREIGN KEY(approved_by) REFERENCES users (id) ON DELETE SET NULL,
                    FOREIGN KEY(tournament_id, group_id) REFERENCES groups (tournament_id, id) ON DELETE SET NULL
                )
            """))
            conn.execute(text("INSERT INTO matches_new SELECT * FROM matches"))
            conn.execute(text("DROP TABLE matches"))
            conn.execute(text("ALTER TABLE matches_new RENAME TO matches"))
            conn.commit()
            print("  完了")

            print("exclusion_pairs テーブルを再作成中...")
            conn.execute(text("""
                CREATE TABLE exclusion_pairs_new (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    tournament_id INTEGER NOT NULL,
                    group_id VARCHAR(1) NOT NULL,
                    team1_id INTEGER NOT NULL,
                    team2_id INTEGER NOT NULL,
                    reason VARCHAR(200),
                    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
                    FOREIGN KEY(tournament_id) REFERENCES tournaments (id) ON DELETE CASCADE,
                    FOREIGN KEY(team1_id) REFERENCES teams (id) ON DELETE CASCADE,
                    FOREIGN KEY(team2_id) REFERENCES teams (id) ON DELETE CASCADE,
                    FOREIGN KEY(tournament_id, group_id) REFERENCES groups (tournament_id, id) ON DELETE CASCADE
                )
            """))
            conn.execute(text("INSERT INTO exclusion_pairs_new SELECT * FROM exclusion_pairs"))
            conn.execute(text("DROP TABLE exclusion_pairs"))
            conn.execute(text("ALTER TABLE exclusion_pairs_new RENAME TO exclusion_pairs"))
            conn.commit()
            print("  完了")

            print("venues テーブルを再作成中...")
            conn.execute(text("""
                CREATE TABLE venues_new (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    tournament_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    address VARCHAR(300),
                    group_id VARCHAR(1),
                    max_matches_per_day INTEGER NOT NULL DEFAULT 6,
                    for_preliminary BOOLEAN NOT NULL DEFAULT 1,
                    for_final_day BOOLEAN NOT NULL DEFAULT 0,
                    notes VARCHAR(500),
                    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                    updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                    FOREIGN KEY(tournament_id) REFERENCES tournaments (id) ON DELETE CASCADE,
                    FOREIGN KEY(tournament_id, group_id) REFERENCES groups (tournament_id, id) ON DELETE SET NULL
                )
            """))
            conn.execute(text("INSERT INTO venues_new SELECT * FROM venues"))
            conn.execute(text("DROP TABLE venues"))
            conn.execute(text("ALTER TABLE venues_new RENAME TO venues"))
            conn.commit()
            print("  完了")

            print("groups テーブルを再作成中...")
            conn.execute(text("""
                CREATE TABLE groups_new (
                    tournament_id INTEGER NOT NULL,
                    id VARCHAR(1) NOT NULL,
                    name VARCHAR(50) NOT NULL,
                    venue_id INTEGER,
                    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                    updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                    PRIMARY KEY (tournament_id, id),
                    FOREIGN KEY(tournament_id) REFERENCES tournaments (id) ON DELETE CASCADE,
                    FOREIGN KEY(venue_id) REFERENCES venues (id) ON DELETE SET NULL
                )
            """))
            conn.execute(text(
                "INSERT INTO groups_new SELECT tournament_id, id, name, venue_id, created_at, updated_at FROM groups"
            ))
            conn.execute(text("DROP TABLE groups"))
            conn.execute(text("ALTER TABLE groups_new RENAME TO groups"))
            conn.commit()
            print("  完了")

            # 外部キー制約を再度有効化
            conn.execute(text("PRAGMA foreign_keys=ON;"))
            conn.commit()

            print("\nマイグレーションが正常に完了しました。")
            return True

        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            print("バックアップからデータベースを復元してください。")
            return False


def main():
    # プロジェクトルートからデータベースパスを計算
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    db_path = os.path.join(project_root, "urawa_cup.db")

    print("=" * 60)
    print("グループテーブル複合主キーマイグレーション")
    print("=" * 60)
    print(f"\nデータベースパス: {db_path}")

    if not os.path.exists(db_path):
        print("\nデータベースファイルが存在しません。")
        print("新規作成時は自動的に複合主キーが適用されます。")
        return

    # バックアップを作成
    print("\n1. バックアップを作成します...")
    backup_path = backup_database(db_path)
    if not backup_path:
        return

    # エンジンを作成
    engine = create_engine(f"sqlite:///{db_path}")

    # マイグレーションが必要かチェック
    print("\n2. マイグレーションが必要かどうか確認します...")
    if not check_migration_needed(engine):
        return

    # ユーザー確認
    print("\n3. マイグレーションを実行します...")
    response = input("続行しますか？ (y/N): ")
    if response.lower() != 'y':
        print("中止しました。")
        return

    # マイグレーション実行
    if run_migration(engine):
        print("\n" + "=" * 60)
        print("マイグレーション完了")
        print("=" * 60)
        print(f"\nバックアップ: {backup_path}")
        print("問題がなければバックアップファイルは削除できます。")
    else:
        print("\nマイグレーションに失敗しました。")
        print(f"バックアップファイル ({backup_path}) から復元してください:")
        print(f"  copy {backup_path} {db_path}")


if __name__ == "__main__":
    main()
