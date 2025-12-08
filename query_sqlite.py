"""Query SQLite database directly"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'zkeco_modern', 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%employee%';")
tables = cursor.fetchall()
print("=== Tables ===")
for table in tables:
    print(f"  {table[0]}")

# Query employee count
cursor.execute("SELECT COUNT(*) FROM legacy_models_employee;")
count = cursor.fetchone()[0]
print(f"\n=== Employee Count ===")
print(f"Total: {count}")

# Get all employees
cursor.execute("SELECT id, userid, firstname, lastname FROM legacy_models_employee ORDER BY userid;")
rows = cursor.fetchall()
print(f"\n=== All Employees ===")
for row in rows:
    print(f"  PK={row[0]}, UserID={row[1]}, Name={row[2]} {row[3]}")

conn.close()
