import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','zkeco_config.local_settings_iaccess')
import django
from django.test import Client

django.setup()
client = Client()
resp = client.get('/iaccess/')
print('status_code=', resp.status_code)
print('content:', resp.content[:200])
