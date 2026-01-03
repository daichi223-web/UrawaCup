"""
浦和カップ トーナメント管理システム - データベース接続設定

SQLAlchemyを使用したDB接続とセッション管理
"""

import os
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from models.base import Base


# プロジェクトルートのパスを取得（backend -> src -> UrawaCup）
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_default_db_path = os.path.join(_project_root, "urawa_cup.db")

# 環境変数からDB設定を取得（デフォルトはSQLite）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{_default_db_path}"
)

# 本番環境用PostgreSQL例:
# DATABASE_URL = "postgresql://user:password@localhost:5432/urawa_cup"

# SQLiteの場合の特別な設定
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        # テスト用にインメモリDBを使う場合はStaticPoolを使用
        # poolclass=StaticPool,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )
    
    # SQLiteで外部キー制約を有効化
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL, MySQLなどの場合
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # 接続の生存確認
        pool_size=5,
        max_overflow=10,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )


# セッションファクトリ
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPIの依存性注入で使用するDB接続取得関数
    
    使用例:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    with文で使用するDB接続取得関数
    
    使用例:
        with get_db_context() as db:
            items = db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    データベースを初期化（テーブル作成）
    
    アプリケーション起動時に呼び出す
    """
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    データベースを削除（テーブル削除）
    
    テスト時のクリーンアップなどに使用
    """
    Base.metadata.drop_all(bind=engine)


def reset_db():
    """
    データベースをリセット（削除後に再作成）
    
    開発時のリセットに使用
    """
    drop_db()
    init_db()


# テスト用のインメモリDBエンジン
def create_test_engine():
    """テスト用のインメモリSQLiteエンジンを作成"""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    return test_engine


def create_test_session(test_engine):
    """テスト用のセッションファクトリを作成"""
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    return TestSessionLocal


# アプリケーション起動時の初期化チェック
if __name__ == "__main__":
    print(f"Database URL: {DATABASE_URL}")
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
