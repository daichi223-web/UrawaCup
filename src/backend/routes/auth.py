"""
認証API

ログイン、トークンリフレッシュ、ユーザー情報取得などのエンドポイント
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User, UserRole
from schemas.user import (
    LoginRequest,
    LoginResponse,
    UserResponse,
    UserCreate,
    UserUpdate,
)
from utils.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    authenticate_user,
    get_current_user,
    get_current_user_optional,
    require_admin,
)


router = APIRouter()


# =====================================================
# 認証エンドポイント
# =====================================================

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    ログイン

    ユーザー名とパスワードで認証し、アクセストークンとリフレッシュトークンを発行

    Args:
        request: ログインリクエスト（username, password）
        db: データベースセッション

    Returns:
        LoginResponse: アクセストークン、リフレッシュトークン、ユーザー情報
    """
    user = authenticate_user(db, request.username, request.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # トークンを生成
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    アクセストークンをリフレッシュ

    リフレッシュトークンを使って新しいアクセストークンを取得

    Args:
        refresh_token: リフレッシュトークン
        db: データベースセッション

    Returns:
        新しいアクセストークンとリフレッシュトークン
    """
    payload = verify_token(refresh_token, "refresh")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="リフレッシュトークンが無効です",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンの形式が不正です",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザーが見つかりません",
        )

    # 新しいトークンを生成
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    現在のユーザー情報を取得

    Args:
        current_user: 認証されたユーザー

    Returns:
        UserResponse: ユーザー情報
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    ログアウト

    クライアント側でトークンを削除することでログアウトを実現。
    サーバー側では特に処理は不要（JWTはステートレス）。

    Note: 将来的にリフレッシュトークンのブラックリスト機能を追加可能。

    Returns:
        ログアウト成功メッセージ
    """
    return {"message": "ログアウトしました"}


# =====================================================
# ユーザー管理エンドポイント（管理者専用）
# =====================================================

@router.get("/users", response_model=list[UserResponse])
async def get_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    ユーザー一覧を取得（管理者専用）

    Args:
        db: データベースセッション
        admin: 管理者ユーザー

    Returns:
        ユーザー一覧
    """
    users = db.query(User).order_by(User.id).all()
    return [UserResponse.model_validate(user) for user in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    ユーザー詳細を取得（管理者専用）

    Args:
        user_id: ユーザーID
        db: データベースセッション
        admin: 管理者ユーザー

    Returns:
        ユーザー詳細
    """
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )

    return UserResponse.model_validate(user)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    ユーザーを作成（管理者専用）

    Args:
        request: ユーザー作成リクエスト
        db: データベースセッション
        admin: 管理者ユーザー

    Returns:
        作成されたユーザー
    """
    # ユーザー名の重複チェック
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="このユーザー名は既に使用されています"
        )

    # パスワードをハッシュ化
    password_hash = hash_password(request.password)

    # ユーザーを作成
    user = User(
        username=request.username,
        password_hash=password_hash,
        display_name=request.display_name,
        email=request.email,
        role=request.role,
        venue_id=request.venue_id,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    ユーザーを更新（管理者専用）

    Args:
        user_id: ユーザーID
        request: ユーザー更新リクエスト
        db: データベースセッション
        admin: 管理者ユーザー

    Returns:
        更新されたユーザー
    """
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )

    # 更新可能なフィールドのみ更新
    if request.display_name is not None:
        user.display_name = request.display_name
    if request.email is not None:
        user.email = request.email
    if request.role is not None:
        user.role = request.role
    if request.venue_id is not None:
        user.venue_id = request.venue_id
    if request.is_active is not None:
        user.is_active = request.is_active

    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    ユーザーを削除（管理者専用）

    Args:
        user_id: ユーザーID
        db: データベースセッション
        admin: 管理者ユーザー
    """
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )

    # 自分自身は削除できない
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="自分自身を削除することはできません"
        )

    db.delete(user)
    db.commit()


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    new_password: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    ユーザーのパスワードをリセット（管理者専用）

    Args:
        user_id: ユーザーID
        new_password: 新しいパスワード
        db: データベースセッション
        admin: 管理者ユーザー

    Returns:
        成功メッセージ
    """
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )

    user.password_hash = hash_password(new_password)
    db.commit()

    return {"message": "パスワードをリセットしました"}


@router.put("/me/password")
async def change_my_password(
    current_password: str,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    自分のパスワードを変更

    Args:
        current_password: 現在のパスワード
        new_password: 新しいパスワード
        db: データベースセッション
        current_user: 現在のユーザー

    Returns:
        成功メッセージ
    """
    from utils.auth import verify_password

    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="現在のパスワードが正しくありません"
        )

    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="パスワードは8文字以上必要です"
        )

    current_user.password_hash = hash_password(new_password)
    db.commit()

    return {"message": "パスワードを変更しました"}
