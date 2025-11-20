"""
Small utility to programmatically render a legacy template and write the result
for inspection. Prints a short success header and path to the rendered file.
Run with the project's virtualenv python and DJANGO_SETTINGS_MODULE/DJANGO_ENV
"""
import os
import sys
from pathlib import Path

# Ensure settings module is set externally; otherwise default to zkeco_config.settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zkeco_config.settings")

try:
    import django
    django.setup()
except Exception as e:
    print("django.setup() failed:", e)
    raise

from django.template import loader
from django.test.client import RequestFactory

OUT = Path(__file__).resolve().parent / "rendered_login.html"

# Provide a request-like object
rf = RequestFactory()
request = rf.get('/')
# supply attributes legacy templates expect
if not hasattr(request, 'surl'):
    request.surl = ''
if not hasattr(request, 'dbapp_url'):
    request.dbapp_url = '/'

# Attempt to locate a login template under configured template dirs.
from django.conf import settings as _s
search_names = [
    'registration/login.html',
    'login.html',
    'iaccess/registration/login.html',
    'iaccess/login.html',
]

found = None
tpl = None
for td in _s.TEMPLATES[0].get('DIRS', []):
    for root, dirs, files in os.walk(td):
        for name in files:
            if name.lower() == 'login.html':
                full = os.path.join(root, name)
                # make a template name relative to the template dir
                rel = os.path.relpath(full, td).replace('\\', '/')
                try:
                    tpl = loader.get_template(rel)
                    found = rel
                    break
                except Exception as e:
                    import traceback
                    print('loader.get_template failed for', rel)
                    print('  full path:', full)
                    print('  exception:', e)
                    print(traceback.format_exc())
                    # try next
                    continue
        if found:
            break
    if found:
        break

if not found:
    print('Could not find legacy template under TEMPLATES DIRS. Tried patterns:', search_names)
    print('TEMPLATE DIRS:', _s.TEMPLATES[0].get('DIRS'))
    sys.exit(2)

try:
    from django.conf import settings as _s
    context = {
        'request': request,
        'MEDIA_URL': getattr(_s, 'MEDIA_URL', '/media'),
        'LANGUAGE_CODE': getattr(_s, 'LANGUAGE_CODE', 'en'),
    }
    rendered = tpl.render(context)
    OUT.write_text(rendered, encoding='utf-8')
    print('Rendered', found, '->', OUT)
    print('Preview (first 512 chars):\n')
    print(rendered[:512])
except Exception as e:
    print('Error rendering template', found, ':', e)
    raise
