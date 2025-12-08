"""Query all employee tables"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'zkeco_modern', 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get columns from agent_employee
cursor.execute("PRAGMA table_info(agent_employee);")
columns = cursor.fetchall()
col_names = [col[1] for col in columns]
print("=== agent_employee columns ===")
for col in col_names[:10]:
    print(f"  {col}")

# Count agent_employee
cursor.execute("SELECT COUNT(*) FROM agent_employee;")
count = cursor.fetchone()[0]
print(f"\n=== agent_employee Count ===")
print(f"Total: {count}")

# Get all from agent_employee
cursor.execute(f"SELECT id, {', '.join(col_names[:5])} FROM agent_employee LIMIT 5;")
rows = cursor.fetchall()
print(f"\n=== First 5 from agent_employee ===")
for row in rows:
    print(f"  {row}")

conn.close()
