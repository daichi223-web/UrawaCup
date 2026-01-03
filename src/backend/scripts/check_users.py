"""ユーザー確認スクリプト"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from models.user import User

db = SessionLocal()

print("=" * 50)
print("ユーザー一覧")
print("=" * 50)

users = db.query(User).all()
if not users:
    print("ユーザーが登録されていません")
else:
    for u in users:
        print(f"ID: {u.id}, Username: {u.username}, Role: {u.role}, Active: {u.is_active}")

db.close()
