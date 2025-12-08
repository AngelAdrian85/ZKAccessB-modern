"""Check audit logs for deletions"""
import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zkeco_modern'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from legacy_models.models import AuditLog

print("=== Audit Log Entries ===")
logs = AuditLog.objects.all().order_by('-timestamp')
print(f'Total audit entries: {logs.count()}')
print('\nRecent entries:')
for log in logs[:10]:
    print(f'{log.timestamp.strftime("%Y-%m-%d %H:%M:%S")} | {log.module:10} | {log.action:6} | {log.entity_name:30} | user: {log.user}')
    if log.details:
        import json
        try:
            details = json.loads(log.details)
            print(f'  Details: {str(details)[:100]}...')
        except:
            print(f'  Details: {log.details[:100]}...')
