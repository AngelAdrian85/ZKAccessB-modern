import os, json
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','zkeco_config.settings')
import django
try:
    django.setup()
except Exception as e:
    print(json.dumps({'ok': False, 'error': f'django.setup failed: {e}'})); raise

from django.test import Client
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    try:
        settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver','localhost','127.0.0.1']
    except Exception:
        settings.ALLOWED_HOSTS = ['testserver','localhost','127.0.0.1']
client = Client(HTTP_HOST='testserver')

# URLs to probe (expand as needed)
urls = [
    '/agent/menu/personnel/',
    '/agent/crud/employees/',
    '/agent/crud/employees/new/',
    '/agent/crud/employees/import/',
    '/personnel/Department/',
    '/personnel/Employee/',
    '/personnel/IssueCard/',
    '/personnel/LeaveLog/',
    '/agent/menu/access/',
    '/agent/crud/doors/',
    '/agent/crud/time-segments/',
    '/agent/crud/holidays/',
    '/agent/crud/access-levels/',
    '/iaccess/AccDoor/',
    '/iaccess/AccFirstOpen/',
    '/agent/menu/reports/',
]

results = {}
for u in urls:
    try:
        resp = client.get(u)
        results[u] = {'status': resp.status_code, 'len': len(resp.content)}
    except Exception as e:
        results[u] = {'status': 'EXC', 'error': str(e)}

print(json.dumps({'ok': True, 'probe': results}, ensure_ascii=False))
