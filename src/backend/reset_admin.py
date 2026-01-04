import sys
import os

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models.user import User
from utils.auth import get_password_hash

def reset_admin():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").first()
        if user:
            print(f"Found user: {user.username}")
            user.hashed_password = get_password_hash("admin1234")
            db.commit()
            print("Password reset to 'admin1234'")
        else:
            print("Admin user not found, creating...")
            user = User(
                username="admin",
                hashed_password=get_password_hash("admin1234"),
                role="admin",
                display_name="Admin"
            )
            db.add(user)
            db.commit()
            print("Admin user created")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin()
