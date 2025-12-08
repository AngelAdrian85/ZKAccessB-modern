"""Test audit logging signals"""
import os
import sys
import django

# Add zkeco_modern to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zkeco_modern'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from legacy_models.models import Employee, AuditLog
from legacy_models.signals import set_current_user
from django.contrib.auth.models import User

# Set user context for audit
user = User.objects.first()
if not user:
    user = User.objects.create_user('testuser', password='test123')
set_current_user(user)

# Get first employee
emp = Employee.objects.first()
print(f'Employee: {emp}')
print(f'Email before: {emp.email}')

# Update employee
emp.email = 'maria.ionescu@test.ro'
emp.FPHONE = '0722123456'
emp.save()

print(f'Email after: {emp.email}')
print(f'Phone after: {emp.FPHONE}')

# Check audit logs
logs = AuditLog.objects.all().order_by('-timestamp')
print(f'\nTotal audit logs: {logs.count()}')
print('\nRecent logs:')
for log in logs[:5]:
    print(f'  {log.timestamp.strftime("%Y-%m-%d %H:%M:%S")} | {log.module} | {log.action} | {log.entity_name}')
    if log.details:
        print(f'    Details: {log.details[:100]}...')
