"""Compare both employee tables"""
import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zkeco_modern'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from agent.models import Employee as AgentEmployee
from legacy_models.models import Employee as LegacyEmployee

print("=== agent.Employee (agent_employee) ===")
agent_count = AgentEmployee.objects.count()
print(f"Count: {agent_count}")
for emp in AgentEmployee.objects.all().order_by('id'):
    print(f"  ID={emp.id}, LegacyUserID={emp.legacy_userid}, {emp.first_name} {emp.last_name}, Card={emp.card_number}")

print("\n=== legacy_models.Employee (legacy_models_employee) ===")
legacy_count = LegacyEmployee.objects.count()
print(f"Count: {legacy_count}")
for emp in LegacyEmployee.objects.all().order_by('userid'):
    print(f"  UserID={emp.userid}, PK={emp.pk}, {emp.firstname} {emp.lastname}, Card={emp.card_number}")

print(f"\n=== SUMMARY ===")
print(f"agent.Employee has {agent_count}, legacy_models.Employee has {legacy_count}")
if agent_count > legacy_count:
    print(f"⚠️  {agent_count - legacy_count} employees in agent_employee NOT synced to legacy_models!")
elif legacy_count > agent_count:
    print(f"⚠️  {legacy_count - agent_count} employees in legacy_models NOT from agent_employee!")
else:
    print("✓ Counts match!")
