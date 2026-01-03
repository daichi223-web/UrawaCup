"""グループテーブルを複合主キー(tournament_id, id)に変更

Revision ID: 001
Revises:
Create Date: 2026-01-01

このマイグレーションは以下の変更を行います:
1. groupsテーブルの主キーを(id)から(tournament_id, id)の複合主キーに変更
2. 関連テーブル(teams, standings, matches, exclusion_pairs, venues)の
   外部キー制約を複合外部キーに変更

注意: 既存のデータベースに適用する前に、必ずバックアップを取得してください。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLiteの場合は外部キー制約を一時的に無効化
    op.execute("PRAGMA foreign_keys=OFF;")

    # 1. teamsテーブルの外部キー制約を削除して再作成
    # 注意: SQLiteでは外部キーの変更はテーブルの再作成が必要

    # teams テーブルの再作成
    op.execute("""
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
    """)
    op.execute("INSERT INTO teams_new SELECT * FROM teams")
    op.execute("DROP TABLE teams")
    op.execute("ALTER TABLE teams_new RENAME TO teams")

    # 2. standings テーブルの再作成
    op.execute("""
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
    """)
    op.execute("INSERT INTO standings_new SELECT * FROM standings")
    op.execute("DROP TABLE standings")
    op.execute("ALTER TABLE standings_new RENAME TO standings")

    # 3. matches テーブルの再作成
    op.execute("""
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
    """)
    op.execute("INSERT INTO matches_new SELECT * FROM matches")
    op.execute("DROP TABLE matches")
    op.execute("ALTER TABLE matches_new RENAME TO matches")

    # 4. exclusion_pairs テーブルの再作成
    op.execute("""
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
    """)
    op.execute("INSERT INTO exclusion_pairs_new SELECT * FROM exclusion_pairs")
    op.execute("DROP TABLE exclusion_pairs")
    op.execute("ALTER TABLE exclusion_pairs_new RENAME TO exclusion_pairs")

    # 5. venues テーブルの再作成
    op.execute("""
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
    """)
    op.execute("INSERT INTO venues_new SELECT * FROM venues")
    op.execute("DROP TABLE venues")
    op.execute("ALTER TABLE venues_new RENAME TO venues")

    # 6. groups テーブルの再作成（複合主キーに変更）
    op.execute("""
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
    """)
    op.execute("INSERT INTO groups_new SELECT tournament_id, id, name, venue_id, created_at, updated_at FROM groups")
    op.execute("DROP TABLE groups")
    op.execute("ALTER TABLE groups_new RENAME TO groups")

    # 外部キー制約を再度有効化
    op.execute("PRAGMA foreign_keys=ON;")


def downgrade() -> None:
    # 警告: downgradeは既存のデータに影響を与える可能性があります
    # 複数の大会が同じグループIDを使用している場合、データ競合が発生します

    op.execute("PRAGMA foreign_keys=OFF;")

    # groups テーブルを単一主キーに戻す
    op.execute("""
        CREATE TABLE groups_new (
            id VARCHAR(1) NOT NULL PRIMARY KEY,
            tournament_id INTEGER NOT NULL,
            name VARCHAR(50) NOT NULL,
            venue_id INTEGER,
            created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
            updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
            FOREIGN KEY(tournament_id) REFERENCES tournaments (id) ON DELETE CASCADE,
            FOREIGN KEY(venue_id) REFERENCES venues (id) ON DELETE SET NULL
        )
    """)
    # 注意: 複数の大会で同じグループIDがある場合、最初の1つだけが残ります
    op.execute("""
        INSERT OR IGNORE INTO groups_new
        SELECT id, tournament_id, name, venue_id, created_at, updated_at
        FROM groups
    """)
    op.execute("DROP TABLE groups")
    op.execute("ALTER TABLE groups_new RENAME TO groups")

    # 関連テーブルの外部キー制約を単一カラムに戻す（省略：手動で実行が必要）

    op.execute("PRAGMA foreign_keys=ON;")
