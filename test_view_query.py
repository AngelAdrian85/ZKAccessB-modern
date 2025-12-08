"""Test employee query like view does"""
import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zkeco_modern'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from legacy_models.models import Employee

# Simulate view query
employees_qs = Employee.objects.select_related('defaultdept').order_by('lastname', 'firstname')

print(f"Total employees: {employees_qs.count()}")
print("\nAll employees:")
for emp in employees_qs:
    print(f"  {emp.userid}: {emp.firstname} {emp.lastname} - {emp.defaultdept.DeptName if emp.defaultdept else 'No Dept'}")
