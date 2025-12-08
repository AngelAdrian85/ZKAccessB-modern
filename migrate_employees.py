"""Migrate employees from agent_employee to legacy_models_employee"""
import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zkeco_modern'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from legacy_models.models import Employee as LegacyEmployee, Dept
from django.db import connection

cursor = connection.cursor()

# Query all from agent_employee
cursor.execute("""
    SELECT id, first_name, last_name, card_number, active, acc_startdate, acc_enddate
    FROM agent_employee
""")
agent_employees = cursor.fetchall()

print(f"Found {len(agent_employees)} employees in agent_employee table")

# Get or create default department
default_dept, _ = Dept.objects.get_or_create(
    code='DEFAULT',
    defaults={'DeptName': 'Default Department'}
)
print(f"Using department: {default_dept.DeptName}")

# Migrate each employee
for row in agent_employees:
    agent_id, first_name, last_name, card_number, active, acc_start, acc_end = row
    
    # Check if already exists
    legacy_emp = LegacyEmployee.objects.filter(userid=agent_id).first()
    if legacy_emp:
        print(f"  ✓ Employee {agent_id} already exists")
        continue
    
    # Create new legacy employee
    emp = LegacyEmployee.objects.create(
        userid=agent_id,
        firstname=first_name or '',
        lastname=last_name or '',
        card_number=card_number,
        defaultdept=default_dept,
        acc_startdate=acc_start,
        acc_enddate=acc_end,
        delayed_door_open=(active == 1)
    )
    print(f"  ✓ Migrated: {emp}")

# Verify
final_count = LegacyEmployee.objects.count()
print(f"\nFinal count in legacy_models_employee: {final_count}")
for emp in LegacyEmployee.objects.all().order_by('userid'):
    print(f"  - UserID={emp.userid}, {emp.firstname} {emp.lastname}, Card={emp.card_number}")
