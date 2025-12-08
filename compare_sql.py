"""Compare both employee tables via SQL"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'zkeco_modern', 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== agent_employee ===")
cursor.execute("SELECT id, legacy_userid, first_name, last_name, card_number FROM agent_employee ORDER BY id")
agent_rows = cursor.fetchall()
print(f"Count: {len(agent_rows)}")
for row in agent_rows:
    emp_id, legacy_uid, first, last, card = row
    print(f"  ID={emp_id}, legacy_userid={legacy_uid}, {first} {last}, Card={card}")

print("\n=== legacy_models_employee ===")
cursor.execute("SELECT id, userid, firstname, lastname, card_number FROM legacy_models_employee ORDER BY userid")
legacy_rows = cursor.fetchall()
print(f"Count: {len(legacy_rows)}")
for row in legacy_rows:
    pk, userid, first, last, card = row
    print(f"  PK={pk}, userid={userid}, {first} {last}, Card={card}")

print(f"\n=== SUMMARY ===")
print(f"agent_employee: {len(agent_rows)}")
print(f"legacy_models_employee: {len(legacy_rows)}")
if len(agent_rows) > len(legacy_rows):
    print(f"⚠️  {len(agent_rows) - len(legacy_rows)} in agent_employee NOT synced!")
elif len(legacy_rows) > len(agent_rows):
    print(f"✓ Extra in legacy_models_employee (already synced/merged)")

conn.close()
