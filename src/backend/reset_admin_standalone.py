import os
import sqlite3
import bcrypt

# DB Path configuration
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_default_db_path = os.path.join(_project_root, "urawa_cup.db")
DATABASE_URL = os.getenv("DATABASE_URL", _default_db_path)

if DATABASE_URL.startswith("sqlite:///"):
    DATABASE_PATH = DATABASE_URL.replace("sqlite:///", "")
else:
    DATABASE_PATH = DATABASE_URL

print(f"Target DB: {DATABASE_PATH}")

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def reset_admin():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id, username FROM users WHERE username = ?", ("admin",))
        user = cursor.fetchone()
        
        new_hash = hash_password("admin1234")
        
        if user:
            print(f"Found user: {user[1]} (ID: {user[0]})")
            # Check is_active
            cursor.execute("SELECT is_active FROM users WHERE username = ?", ("admin",))
            active = cursor.fetchone()[0]
            print(f"Current is_active: {active}")
            
            cursor.execute("UPDATE users SET password_hash = ?, is_active = 1 WHERE username = ?", (new_hash, "admin"))
            print("Password updated and is_active set to 1.")
        else:
            print("Admin user not found. Creating...")
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, display_name, is_active) VALUES (?, ?, ?, ?, ?)",
                ("admin", new_hash, "admin", "Admin", 1)
            )
            print("Admin user created.")
            
        conn.commit()
        conn.close()
        print("Success.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reset_admin()
