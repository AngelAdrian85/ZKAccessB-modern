import os
import sys
import django
from django.test import RequestFactory

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'zkeco_config.settings'
repo_mod = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'zkeco_modern'))
if os.path.isdir(repo_mod) and repo_mod not in sys.path:
    sys.path.insert(0, repo_mod)

django.setup()

from django.template.loader import get_template
from django.conf import settings

req = RequestFactory().get('/iaccess/test/')
# ensure request has expected attributes
if not hasattr(req, 'surl'):
    req.surl = ''
if not hasattr(req, 'dbapp_url'):
    req.dbapp_url = '/'

name = 'iaccess/test.html'
print('Loading template', name)
try:
    tpl = get_template(name)
    print('Template loaded, source snippet:\n', getattr(tpl, 'template', repr(tpl))[:400])
    rendered = tpl.render({'request': req}, request=req)
    print('Rendered:\n', rendered[:1000])
except Exception as e:
    import traceback
    traceback.print_exc()
    print('Error:', e)
