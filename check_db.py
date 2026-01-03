import sqlite3

conn = sqlite3.connect("D:/UrawaCup/urawa_cup.db")
c = conn.cursor()

# List tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]
print("Tables:", tables)

# Check standings
c.execute("SELECT COUNT(*) FROM standings")
print("Standings count:", c.fetchone()[0])

# Check groups
c.execute("SELECT * FROM groups")
groups = c.fetchall()
print("Groups:", groups)

conn.close()
