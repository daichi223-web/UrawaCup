"""
浦和カップ トーナメント管理システム - テスト共通設定

pytest fixtures と共通セットアップ
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import get_db
from backend.models.base import Base


# テスト用のインメモリSQLiteエンジン
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """各テスト用にクリーンなDBエンジンを作成"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # SQLiteで外部キー制約を有効化
    from sqlalchemy import event, text

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # テーブルを作成
    Base.metadata.create_all(bind=engine)

    yield engine

    # テスト後にテーブルを削除（外部キー制約を一時無効化）
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        conn.commit()

    try:
        Base.metadata.drop_all(bind=engine)
    except Exception:
        # ドロップ失敗時は無視（インメモリDBは破棄されるため）
        pass


@pytest.fixture(scope="function")
def test_session(test_engine):
    """テスト用DBセッション"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_session):
    """テスト用FastAPIクライアント"""

    def override_get_db():
        try:
            yield test_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_tournament_data():
    """サンプル大会データ"""
    return {
        "name": "第42回さいたま市招待高校サッカーフェスティバル浦和カップ",
        "edition": 42,
        "year": 2024,
        "start_date": "2024-03-25",
        "end_date": "2024-03-27",
        "match_duration": 50,
        "half_duration": 25,
        "interval_minutes": 15,
    }


@pytest.fixture
def sample_teams_data():
    """サンプルチームデータ（地元校4校）"""
    return [
        {
            "name": "浦和南高校",
            "short_name": "浦和南",
            "team_type": "local",
            "is_venue_host": True,
            "prefecture": "埼玉県",
        },
        {
            "name": "市立浦和高校",
            "short_name": "市浦和",
            "team_type": "local",
            "is_venue_host": True,
            "prefecture": "埼玉県",
        },
        {
            "name": "浦和学院高校",
            "short_name": "浦学",
            "team_type": "local",
            "is_venue_host": True,
            "prefecture": "埼玉県",
        },
        {
            "name": "武南高校",
            "short_name": "武南",
            "team_type": "local",
            "is_venue_host": True,
            "prefecture": "埼玉県",
        },
    ]


@pytest.fixture
def sample_venues_data():
    """サンプル会場データ"""
    return [
        {
            "name": "浦和南高校グラウンド",
            "address": "さいたま市南区",
            "max_matches_per_day": 6,
            "for_preliminary": True,
            "for_final_day": False,
        },
        {
            "name": "市立浦和高校グラウンド",
            "address": "さいたま市浦和区",
            "max_matches_per_day": 6,
            "for_preliminary": True,
            "for_final_day": False,
        },
        {
            "name": "浦和学院高校グラウンド",
            "address": "さいたま市緑区",
            "max_matches_per_day": 6,
            "for_preliminary": True,
            "for_final_day": False,
        },
        {
            "name": "武南高校グラウンド",
            "address": "蕨市",
            "max_matches_per_day": 6,
            "for_preliminary": True,
            "for_final_day": False,
        },
        {
            "name": "浦和駒場スタジアム",
            "address": "さいたま市浦和区駒場",
            "max_matches_per_day": 4,
            "for_preliminary": False,
            "for_final_day": True,
        },
    ]
