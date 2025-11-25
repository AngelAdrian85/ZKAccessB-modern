import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = 'zkeco_config.settings'
import django
django.setup()
from django.test import Client
client = Client()
resp = client.get('/oauth-debug/', {'code': 'TEST', 'state': 'XYZ'})
print('---OAUTH-DEBUG-RESULT---')
print('STATUS:' , resp.status_code)
print('LENGTH:' , len(resp.content))
print('BODY_PREVIEW:')
data = resp.content.decode('utf-8', errors='replace')
print(data[:1000])
print('---END---')
