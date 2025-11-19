import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','zkeco_config.local_settings_iaccess')
import django
from django.urls import resolve, Resolver404
django.setup()
try:
    r = resolve('/iaccess/')
    print('resolved:', r.func, 'args:', r.args, 'kwargs:', r.kwargs, 'url_name:', r.url_name)
except Resolver404:
    print('no match for /iaccess/')
