"""Fix employee data from agent_employee"""
import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zkeco_modern'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from legacy_models.models import Employee as LegacyEmployee
from django.db import connection

cursor = connection.cursor()

# Get all from agent_employee
cursor.execute("""
    SELECT id, first_name, last_name, card_number, active, acc_startdate, acc_enddate
    FROM agent_employee
    ORDER BY id
""")
agent_employees = cursor.fetchall()

print("=== Syncing employees from agent_employee ===\n")

for agent_id, first_name, last_name, card_number, active, acc_start, acc_end in agent_employees:
    emp = LegacyEmployee.objects.filter(userid=agent_id).first()
    if emp:
        # Update existing
        old_name = f"{emp.firstname} {emp.lastname}"
        new_name = f"{first_name} {last_name}"
        
        emp.firstname = first_name or ''
        emp.lastname = last_name or ''
        emp.card_number = card_number
        emp.acc_startdate = acc_start
        emp.acc_enddate = acc_end
        emp.save()
        
        if old_name != new_name:
            print(f"✓ Updated UserID={agent_id}: '{old_name}' → '{new_name}'")
        else:
            print(f"✓ Verified UserID={agent_id}: {new_name}")
    else:
        print(f"✗ Missing UserID={agent_id}: {first_name} {last_name}")

print("\n=== Final result ===")
for emp in LegacyEmployee.objects.all().order_by('userid'):
    print(f"  UserID={emp.userid}, {emp.firstname} {emp.lastname}, Card={emp.card_number}, Dept={emp.defaultdept.DeptName if emp.defaultdept else 'None'}")
