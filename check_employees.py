"""Check employees in database"""
import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zkeco_modern'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from legacy_models.models import Employee

emp_count = Employee.objects.count()
print(f'Total employees: {emp_count}')
print('\nAll employees:')
for emp in Employee.objects.all().order_by('userid'):
    print(f'  PK={emp.pk}, UserID={emp.userid}, Name={emp.firstname} {emp.lastname}, Dept={emp.defaultdept.DeptName if emp.defaultdept else None}, Card={emp.card_number}')
