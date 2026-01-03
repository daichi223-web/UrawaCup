"""管理者パスワードリセットスクリプト"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import bcrypt
from database import SessionLocal
from models.user import User

db = SessionLocal()

admin = db.query(User).filter(User.username == "admin").first()
if admin:
    new_password = "admin123"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(new_password.encode("utf-8"), salt)
    admin.password_hash = hashed.decode("utf-8")
    db.commit()
    print(f"パスワードをリセットしました")
    print(f"  ユーザー名: admin")
    print(f"  パスワード: {new_password}")
else:
    print("adminユーザーが見つかりません")

db.close()
