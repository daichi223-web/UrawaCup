import sqlite3
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

# from src.backend.config import Settings

def migrate():
    """Add short_name column to tournaments table"""
    db_path = "d:/UrawaCup/urawa_cup.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    print(f"Connecting to database at {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in database: {tables}")

        # Check if column already exists
        cursor.execute("PRAGMA table_info(tournaments)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'short_name' in columns:
            print("Column 'short_name' already exists in 'tournaments' table.")
        else:
            print("Adding 'short_name' column to 'tournaments' table...")
            cursor.execute("ALTER TABLE tournaments ADD COLUMN short_name TEXT")
            print("Column added successfully.")
            
        conn.commit()
    except Exception as e:
        print(f"Error migrating database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
