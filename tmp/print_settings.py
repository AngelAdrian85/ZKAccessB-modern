import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','zkeco_config.local_settings_iaccess')
import django
from django.conf import settings
django.setup()
print('DJANGO_SETTINGS_MODULE=', os.environ.get('DJANGO_SETTINGS_MODULE'))
print('ROOT_URLCONF=', settings.ROOT_URLCONF)
print('INSTALLED_APPS contains iaccess_port? ', 'iaccess_port' in settings.INSTALLED_APPS)
