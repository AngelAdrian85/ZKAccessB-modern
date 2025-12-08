"""Query full details from agent_employee"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'zkeco_modern', 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT id, first_name, last_name, card_number, active, acc_startdate, acc_enddate
    FROM agent_employee
    ORDER BY id
""")
rows = cursor.fetchall()
print("=== All agent_employee records ===")
for row in rows:
    emp_id, fname, lname, card, active, acc_start, acc_end = row
    print(f"ID={emp_id}: {fname} {lname}, Card={card}, Active={active}")
    print(f"         Start={acc_start}, End={acc_end}")

conn.close()
