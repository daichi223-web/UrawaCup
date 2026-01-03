#!/usr/bin/env python
"""
管理者ユーザー作成スクリプト

初期セットアップ時に管理者ユーザーを作成するためのスクリプト。

使用方法:
    # デフォルト設定で管理者を作成（admin / admin1234）
    python scripts/create_admin.py

    # カスタム設定で管理者を作成
    python scripts/create_admin.py admin パスワード 管理者名

    # インタラクティブモード
    python scripts/create_admin.py --interactive
"""

import sys
import os
import argparse
from getpass import getpass

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.user import User, UserRole
from utils.auth import hash_password


def create_admin(username: str, password: str, display_name: str, venue_id: int = None) -> bool:
    """
    管理者ユーザーを作成

    Args:
        username: ユーザー名
        password: パスワード
        display_name: 表示名
        venue_id: 担当会場ID（オプション）

    Returns:
        作成成功時True、既存ユーザー時False
    """
    db = SessionLocal()
    try:
        # 既存ユーザーチェック
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"エラー: ユーザー '{username}' は既に存在します")
            return False

        # 管理者ユーザー作成
        admin = User(
            username=username,
            password_hash=hash_password(password),
            display_name=display_name,
            role=UserRole.ADMIN,
            venue_id=venue_id,
            is_active=True,
        )
        db.add(admin)
        db.commit()

        print(f"✓ 管理者 '{username}' を作成しました")
        print(f"  - 表示名: {display_name}")
        print(f"  - 権限: 管理者 (admin)")
        return True

    except Exception as e:
        db.rollback()
        print(f"エラー: 管理者の作成に失敗しました: {e}")
        return False
    finally:
        db.close()


def create_venue_staff(username: str, password: str, display_name: str, venue_id: int) -> bool:
    """
    会場担当者ユーザーを作成

    Args:
        username: ユーザー名
        password: パスワード
        display_name: 表示名
        venue_id: 担当会場ID

    Returns:
        作成成功時True、既存ユーザー時False
    """
    db = SessionLocal()
    try:
        # 既存ユーザーチェック
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"エラー: ユーザー '{username}' は既に存在します")
            return False

        # 会場担当者ユーザー作成
        staff = User(
            username=username,
            password_hash=hash_password(password),
            display_name=display_name,
            role=UserRole.VENUE_STAFF,
            venue_id=venue_id,
            is_active=True,
        )
        db.add(staff)
        db.commit()

        print(f"✓ 会場担当者 '{username}' を作成しました")
        print(f"  - 表示名: {display_name}")
        print(f"  - 担当会場ID: {venue_id}")
        return True

    except Exception as e:
        db.rollback()
        print(f"エラー: 会場担当者の作成に失敗しました: {e}")
        return False
    finally:
        db.close()


def interactive_mode():
    """インタラクティブモードでユーザーを作成"""
    print("=" * 50)
    print("浦和カップ - ユーザー作成ウィザード")
    print("=" * 50)
    print()

    # ユーザー種別選択
    print("ユーザー種別を選択してください:")
    print("  1. 管理者 (admin)")
    print("  2. 会場担当者 (venue_staff)")
    print()

    choice = input("選択 [1]: ").strip() or "1"
    is_admin = choice == "1"

    # 基本情報入力
    username = input("ユーザー名: ").strip()
    if not username:
        print("エラー: ユーザー名は必須です")
        return False

    password = getpass("パスワード (8文字以上): ")
    if len(password) < 8:
        print("エラー: パスワードは8文字以上必要です")
        return False

    password_confirm = getpass("パスワード (確認): ")
    if password != password_confirm:
        print("エラー: パスワードが一致しません")
        return False

    display_name = input("表示名: ").strip()
    if not display_name:
        display_name = username

    venue_id = None
    if not is_admin:
        venue_id_str = input("担当会場ID: ").strip()
        if venue_id_str:
            try:
                venue_id = int(venue_id_str)
            except ValueError:
                print("エラー: 会場IDは数値で入力してください")
                return False

    # 確認
    print()
    print("-" * 50)
    print("以下の内容でユーザーを作成します:")
    print(f"  - ユーザー名: {username}")
    print(f"  - 表示名: {display_name}")
    print(f"  - 権限: {'管理者' if is_admin else '会場担当者'}")
    if venue_id:
        print(f"  - 担当会場ID: {venue_id}")
    print("-" * 50)

    confirm = input("作成しますか？ [y/N]: ").strip().lower()
    if confirm != "y":
        print("キャンセルしました")
        return False

    # 作成
    if is_admin:
        return create_admin(username, password, display_name, venue_id)
    else:
        if venue_id is None:
            print("エラー: 会場担当者には担当会場IDが必要です")
            return False
        return create_venue_staff(username, password, display_name, venue_id)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="浦和カップ - 管理者ユーザー作成スクリプト"
    )
    parser.add_argument(
        "username",
        nargs="?",
        default="admin",
        help="ユーザー名 (デフォルト: admin)"
    )
    parser.add_argument(
        "password",
        nargs="?",
        default="admin1234",
        help="パスワード (デフォルト: admin1234)"
    )
    parser.add_argument(
        "display_name",
        nargs="?",
        default="システム管理者",
        help="表示名 (デフォルト: システム管理者)"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="インタラクティブモードで実行"
    )
    parser.add_argument(
        "-v", "--venue-id",
        type=int,
        default=None,
        help="担当会場ID（オプション）"
    )

    args = parser.parse_args()

    if args.interactive:
        success = interactive_mode()
    else:
        print("浦和カップ - 管理者作成")
        print("-" * 30)
        success = create_admin(
            args.username,
            args.password,
            args.display_name,
            args.venue_id
        )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
