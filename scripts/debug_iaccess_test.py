import os
import sys
import django
from django.test import Client

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'zkeco_config.settings'
repo_mod = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'zkeco_modern'))
if os.path.isdir(repo_mod) and repo_mod not in sys.path:
    sys.path.insert(0, repo_mod)

django.setup()

from django.conf import settings as _dj_settings
# ensure testserver allowed
try:
    current = list(getattr(_dj_settings, 'ALLOWED_HOSTS', []) or [])
except Exception:
    current = []
for _h in ('testserver', 'localhost', '127.0.0.1'):
    if _h not in current:
        current.append(_h)
try:
    _dj_settings.ALLOWED_HOSTS = current
except Exception:
    pass

client = Client()

path = '/iaccess/test/'
print('Requesting', path)
try:
    resp = client.get(path)
    print('Status:', resp.status_code)
    print(resp.content.decode('utf-8', errors='replace'))
except Exception as e:
    import traceback
    traceback.print_exc()
    print('Exception:', e)
