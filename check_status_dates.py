"""Check employee status dates"""
import os
import sys
import django
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zkeco_modern'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from legacy_models.models import Employee

today = date.today()
print(f"Today: {today}")
print("\nEmployee dates:")
for emp in Employee.objects.all().order_by('userid'):
    print(f"  UserID={emp.userid}, {emp.firstname} {emp.lastname}")
    print(f"    acc_startdate: {emp.acc_startdate}")
    print(f"    acc_enddate: {emp.acc_enddate}")
    if emp.acc_enddate:
        is_active = emp.acc_enddate >= today
        print(f"    Status: {'ACTIV' if is_active else 'INACTIV'} (acc_enddate >= today)")
    else:
        print(f"    Status: INACTIV (no end date)")
