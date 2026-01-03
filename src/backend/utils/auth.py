"""
浦和カップ トーナメント管理システム - 認証・認可ユーティリティ

JWT認証、パスワードハッシュ、権限チェック機能を提供
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from functools import wraps

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.user import User, UserRole


# パスワードハッシュ用コンテキスト

# HTTPベアラー認証スキーム
security = HTTPBearer(auto_error=False)


# =====================================================
# パスワード関連
# =====================================================

def hash_password(password: str) -> str:
    """
    パスワードをハッシュ化

    Args:
        password: プレーンテキストのパスワード

    Returns:
        ハッシュ化されたパスワード
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    パスワードを検証

    Args:
        plain_password: プレーンテキストのパスワード
        hashed_password: ハッシュ化されたパスワード

    Returns:
        パスワードが一致すればTrue
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# =====================================================
# JWT トークン関連
# =====================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    アクセストークンを生成

    Args:
        data: トークンに含めるデータ（通常はsub=user_id）
        expires_delta: 有効期限（デフォルト: 設定値）

    Returns:
        JWTアクセストークン
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc),
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return encoded_jwt


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    リフレッシュトークンを生成

    Args:
        data: トークンに含めるデータ（通常はsub=user_id）
        expires_delta: 有効期限（デフォルト: 7日間）

    Returns:
        JWTリフレッシュトークン
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # リフレッシュトークンは7日間有効
        expire = datetime.now(timezone.utc) + timedelta(days=7)

    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    トークンを検証してペイロードを返す

    Args:
        token: JWTトークン
        token_type: 期待するトークンタイプ（"access" または "refresh"）

    Returns:
        ペイロード辞書、無効な場合はNone
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        # トークンタイプの検証
        if payload.get("type") != token_type:
            return None

        return payload
    except JWTError:
        return None


# =====================================================
# FastAPI 依存性注入
# =====================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    現在のユーザーを取得（認証必須）

    FastAPIの依存性注入として使用。
    Authorization: Bearer <token> ヘッダーが必要。

    開発モード（DEV_MODE=true）では認証をスキップして管理者を返す。

    Args:
        credentials: HTTPベアラー認証情報
        db: データベースセッション

    Returns:
        認証されたUserオブジェクト

    Raises:
        HTTPException: 認証失敗時（401）
    """
    import os

    # 開発モード: 認証をスキップして管理者ユーザーを返す
    if os.getenv("DEV_MODE", "false").lower() == "true":
        admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin_user:
            return admin_user

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報が無効です",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    payload = verify_token(token, "access")

    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このアカウントは無効化されています"
        )

    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    現在のユーザーを取得（認証オプション）

    認証がなくてもエラーにならない。
    閲覧系APIで使用。

    Args:
        credentials: HTTPベアラー認証情報（オプション）
        db: データベースセッション

    Returns:
        認証されたUserオブジェクト、未認証の場合はNone
    """
    if credentials is None:
        return None

    token = credentials.credentials
    payload = verify_token(token, "access")

    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None or not user.is_active:
        return None

    return user


# =====================================================
# 権限チェック依存性
# =====================================================

async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    管理者権限を要求

    Args:
        current_user: 認証されたユーザー

    Returns:
        管理者権限を持つUserオブジェクト

    Raises:
        HTTPException: 管理者権限がない場合（403）
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です"
        )
    return current_user


class RequireVenueManager:
    """
    会場担当者権限を要求するクラス

    指定された会場の編集権限を持つユーザーのみアクセス可能。
    管理者は全ての会場にアクセス可能。

    Usage:
        @router.post("/matches/{match_id}/score")
        async def update_score(
            match_id: int,
            user: User = Depends(RequireVenueManager())
        ):
            ...
    """

    def __init__(self, venue_id_param: str = "venue_id"):
        """
        Args:
            venue_id_param: パスパラメータ名（デフォルト: venue_id）
        """
        self.venue_id_param = venue_id_param

    async def __call__(
        self,
        current_user: User = Depends(get_current_user)
    ) -> User:
        """
        ユーザーの会場管理権限をチェック

        Note: 実際の会場IDチェックはルート内で行う必要あり
        """
        if current_user.role not in [UserRole.ADMIN, UserRole.VENUE_STAFF]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この操作には会場担当者以上の権限が必要です"
            )
        return current_user


# シンプルな依存性として使用する場合
async def require_venue_manager(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    会場担当者以上の権限を要求

    Args:
        current_user: 認証されたユーザー

    Returns:
        会場担当者以上の権限を持つUserオブジェクト

    Raises:
        HTTPException: 権限がない場合（403）
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.VENUE_STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には会場担当者以上の権限が必要です"
        )
    return current_user


def check_venue_permission(user: User, venue_id: int) -> None:
    """
    ユーザーが指定会場の編集権限を持つかチェック

    Args:
        user: ユーザー
        venue_id: 会場ID

    Raises:
        HTTPException: 権限がない場合（403）
    """
    if not user.can_edit_venue(venue_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この会場を編集する権限がありません"
        )


def check_match_permission(user: User, match) -> None:
    """
    ユーザーが指定試合の編集権限を持つかチェック

    Args:
        user: ユーザー
        match: 試合オブジェクト

    Raises:
        HTTPException: 権限がない場合（403）
    """
    if not user.can_edit_match(match):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この試合を編集する権限がありません"
        )


# =====================================================
# ユーザー認証ヘルパー
# =====================================================

def authenticate_user(
    db: Session,
    username: str,
    password: str
) -> Optional[User]:
    """
    ユーザー認証を行う

    Args:
        db: データベースセッション
        username: ユーザー名
        password: パスワード

    Returns:
        認証成功時はUserオブジェクト、失敗時はNone
    """
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    if not user.is_active:
        return None

    return user
