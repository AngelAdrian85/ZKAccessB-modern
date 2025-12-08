"""Fix legacy_userid in agent_employee to match legacy_models"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'zkeco_modern', 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Fixing legacy_userid in agent_employee ===\n")

# Get all agent_employee records
cursor.execute("SELECT id, first_name, last_name FROM agent_employee")
agent_emps = cursor.fetchall()

for agent_id, first_name, last_name in agent_emps:
    # Find matching legacy employee
    cursor.execute("""
        SELECT userid FROM legacy_models_employee 
        WHERE firstname = ? AND lastname = ?
        LIMIT 1
    """, (first_name, last_name))
    result = cursor.fetchone()
    
    if result:
        legacy_userid = result[0]
        # Get current legacy_userid
        cursor.execute("SELECT legacy_userid FROM agent_employee WHERE id = ?", (agent_id,))
        current = cursor.fetchone()[0]
        
        if current != legacy_userid:
            cursor.execute(
                "UPDATE agent_employee SET legacy_userid = ? WHERE id = ?",
                (legacy_userid, agent_id)
            )
            print(f"  ✓ agent ID {agent_id}: {first_name} {last_name}")
            print(f"    legacy_userid: {current} → {legacy_userid}")
        else:
            print(f"  ✓ agent ID {agent_id}: {first_name} {last_name} - already correct")

conn.commit()
conn.close()

print("\n=== Verification ===")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT a.id, a.legacy_userid, a.first_name, a.last_name, l.userid, l.firstname, l.lastname
    FROM agent_employee a
    LEFT JOIN legacy_models_employee l ON a.legacy_userid = l.userid
    ORDER BY a.id
""")

for row in cursor.fetchall():
    agent_id, legacy_uid, agent_first, agent_last, legacy_uid2, legacy_first, legacy_last = row
    match = "✓" if legacy_uid == legacy_uid2 else "✗"
    print(f"{match} agent ID {agent_id}: legacy_userid={legacy_uid}, matches legacy userid={legacy_uid2}")

conn.close()
