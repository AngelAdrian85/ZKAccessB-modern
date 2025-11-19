import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','zkeco_config.local_settings_iaccess')
import django
from django.urls import get_resolver

django.setup()
res = get_resolver()
for i,p in enumerate(res.url_patterns):
    try:
        name = getattr(p, 'urlconf_name', None)
    except Exception:
        name = None
    print(i, 'pattern:', str(p.pattern), 'repr:', repr(p), 'urlconf_name:', name)
    try:
        # try to inspect included urlconf module
        if hasattr(p, 'url_patterns'):
            print('  nested count:', len(p.url_patterns))
    except Exception:
        pass
