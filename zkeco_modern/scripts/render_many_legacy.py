"""
Render many legacy templates and report missing media assets per page.
Saves rendered pages under `scripts/rendered_pages/`.
Run from `zkeco_modern` directory with the project's venv and
`DJANGO_SETTINGS_MODULE='zkeco_config.settings'` and `INCLUDE_LEGACY=1`.

Example:
  $env:INCLUDE_LEGACY='1'; $env:DJANGO_SETTINGS_MODULE='zkeco_config.settings'; .venv\Scripts\python.exe scripts\render_many_legacy.py
"""
import os
import re
import sys
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
try:
    import django
    django.setup()
except Exception as e:
    print('django.setup() failed:', e)
    raise

from django.template import loader
from django.test.client import RequestFactory
from django.conf import settings

OUT_DIR = Path(__file__).resolve().parent / 'rendered_pages'
OUT_DIR.mkdir(parents=True, exist_ok=True)

rf = RequestFactory()
request = rf.get('/')
if not hasattr(request, 'surl'):
    request.surl = ''
if not hasattr(request, 'dbapp_url'):
    request.dbapp_url = '/'

media_root = getattr(settings, 'MEDIA_ROOT', None)
media_url = getattr(settings, 'MEDIA_URL', '/media/')
if media_root is None:
    print('MEDIA_ROOT is not configured in settings; aborting')
    sys.exit(2)

asset_re = re.compile(r'(?:src|href)=["\']([^"\']+)["\']')

summary = []
any_missing = False

# Walk template dirs and find .html files
template_dirs = []
for td in settings.TEMPLATES[0].get('DIRS', []):
    template_dirs.append(td)

if not template_dirs:
    print('No template DIRS configured to search.')
    sys.exit(2)

print('Scanning template dirs:', template_dirs)

for td in template_dirs:
    for root, dirs, files in os.walk(td):
        for fn in files:
            if not fn.lower().endswith('.html'):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, td).replace('\\', '/')
            page_safe = rel.replace('/', '__')
            out_path = OUT_DIR / (page_safe)
            record = {'template': rel, 'rendered': str(out_path), 'missing': [], 'error': None}
            try:
                tpl = loader.get_template(rel)
            except Exception as e:
                record['error'] = f'get_template failed: {e}'
                summary.append(record)
                continue
            try:
                context = {'request': request, 'MEDIA_URL': media_url, 'LANGUAGE_CODE': getattr(settings, 'LANGUAGE_CODE', 'en')}
                # pass the request to render so template context processors (like csrf) are applied
                rendered = tpl.render(context, request=request)
                out_path.write_text(rendered, encoding='utf-8')
                # scan assets
                urls = asset_re.findall(rendered)
                for u in urls:
                    if u.startswith(media_url) or u.startswith('/media/'):
                        relu = u[len(media_url):] if u.startswith(media_url) else u.lstrip('/')
                        relu = relu.lstrip('/')
                        abspath = os.path.join(media_root, relu)
                        if not os.path.exists(abspath):
                            record['missing'].append({'url': u, 'path': abspath})
                if record['missing']:
                    any_missing = True
                summary.append(record)
                print('Rendered', rel, '->', out_path, 'missing:', len(record['missing']))
            except Exception as e:
                record['error'] = f'render failed: {e}'
                summary.append(record)
                print('Error rendering', rel, e)

# Print a concise report
print('\nSummary:')
for r in summary:
    if r['error']:
        print(f"- {r['template']}: ERROR: {r['error']}")
    else:
        print(f"- {r['template']}: rendered -> {r['rendered']}, missing assets: {len(r['missing'])}")
        for m in r['missing'][:10]:
            print(f"    missing {m['url']} -> {m['path']}")

if any_missing:
    print('\nSome pages have missing assets. See details above and check MEDIA_ROOT.')
    sys.exit(3)
else:
    print('\nAll rendered pages referenced existing media assets.')
    sys.exit(0)
"""
Render many legacy templates and report missing media assets per page.
Saves rendered pages under `scripts/rendered_pages/`.
Run from `zkeco_modern` directory with the project's venv and
`DJANGO_SETTINGS_MODULE='zkeco_config.settings'` and `INCLUDE_LEGACY=1`.

Example:
  $env:INCLUDE_LEGACY='1'; $env:DJANGO_SETTINGS_MODULE='zkeco_config.settings'; .venv\Scripts\python.exe scripts\render_many_legacy.py
"""
import os
import re
import sys
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
try:
    import django
    django.setup()
except Exception as e:
    print('django.setup() failed:', e)
    raise

from django.template import loader
from django.test.client import RequestFactory
from django.conf import settings

OUT_DIR = Path(__file__).resolve().parent / 'rendered_pages'
OUT_DIR.mkdir(parents=True, exist_ok=True)

rf = RequestFactory()
request = rf.get('/')
if not hasattr(request, 'surl'):
    request.surl = ''
if not hasattr(request, 'dbapp_url'):
    request.dbapp_url = '/'

media_root = getattr(settings, 'MEDIA_ROOT', None)
media_url = getattr(settings, 'MEDIA_URL', '/media/')
if media_root is None:
    print('MEDIA_ROOT is not configured in settings; aborting')
    sys.exit(2)

asset_re = re.compile(r'(?:src|href)=["\']([^"\']+)["\']')

summary = []
any_missing = False

# Walk template dirs and find .html files
template_dirs = []
for td in settings.TEMPLATES[0].get('DIRS', []):
    template_dirs.append(td)

if not template_dirs:
    print('No template DIRS configured to search.')
    sys.exit(2)

print('Scanning template dirs:', template_dirs)

for td in template_dirs:
    for root, dirs, files in os.walk(td):
        for fn in files:
            if not fn.lower().endswith('.html'):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, td).replace('\\', '/')
            page_safe = rel.replace('/', '__')
            out_path = OUT_DIR / (page_safe)
            record = {'template': rel, 'rendered': str(out_path), 'missing': [], 'error': None}
            try:
                tpl = loader.get_template(rel)
            except Exception as e:
                record['error'] = f'get_template failed: {e}'
                summary.append(record)
                continue
            try:
                context = {'request': request, 'MEDIA_URL': media_url, 'LANGUAGE_CODE': getattr(settings, 'LANGUAGE_CODE', 'en')}
                # pass the request to render so template context processors (like csrf) are applied
                rendered = tpl.render(context, request=request)
                out_path.write_text(rendered, encoding='utf-8')
                # scan assets
                urls = asset_re.findall(rendered)
                for u in urls:
                    if u.startswith(media_url) or u.startswith('/media/'):
                        relu = u[len(media_url):] if u.startswith(media_url) else u.lstrip('/')
                        relu = relu.lstrip('/')
                        abspath = os.path.join(media_root, relu)
                        if not os.path.exists(abspath):
                            record['missing'].append({'url': u, 'path': abspath})
                if record['missing']:
                    any_missing = True
                summary.append(record)
                print('Rendered', rel, '->', out_path, 'missing:', len(record['missing']))
            except Exception as e:
                record['error'] = f'render failed: {e}'
                summary.append(record)
                print('Error rendering', rel, e)

# Print a concise report
print('\nSummary:')
for r in summary:
    if r['error']:
        print(f"- {r['template']}: ERROR: {r['error']}")
    else:
        print(f"- {r['template']}: rendered -> {r['rendered']}, missing assets: {len(r['missing'])}")
        for m in r['missing'][:10]:
            print(f"    missing {m['url']} -> {m['path']}")

if any_missing:
    print('\nSome pages have missing assets. See details above and check MEDIA_ROOT.')
    sys.exit(3)
else:
    print('\nAll rendered pages referenced existing media assets.')
    sys.exit(0)
