import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','zkeco_config.local_settings_iaccess')
import django
from django.urls import resolve, Resolver404, get_resolver
django.setup()
try:
    r = resolve('/iaccess/')
    print('resolved:', r)
except Resolver404:
    print('no match for /iaccess/')
res = get_resolver()
for i,p in enumerate(res.url_patterns):
    print(i, repr(p), str(p.pattern))
