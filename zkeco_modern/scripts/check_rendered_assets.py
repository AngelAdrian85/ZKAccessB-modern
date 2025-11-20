"""
Check assets referenced in scripts/rendered_login.html and report missing files under MEDIA_ROOT.
Run from the project dir with the same DJANGO_SETTINGS_MODULE used for rendering.
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
from django.conf import settings

OUT = Path(__file__).resolve().parent / 'rendered_login.html'
if not OUT.exists():
    print('Rendered file not found:', OUT)
    sys.exit(2)

text = OUT.read_text(encoding='utf-8')
# find src/href values
pattern = re.compile(r'(?:src|href)=["\']([^"\']+)["\']')
urls = pattern.findall(text)
# normalize media root
media_root = getattr(settings, 'MEDIA_ROOT', None)
media_url = getattr(settings, 'MEDIA_URL', '/media/')
if media_root is None:
    print('MEDIA_ROOT is not configured in settings')
    sys.exit(2)

found = []
missing = []
for u in urls:
    if u.startswith(media_url) or u.startswith('/media/'):
        # strip leading media_url
        rel = u[len(media_url):] if u.startswith(media_url) else u.lstrip('/')
        # remove leading slash if present
        rel = rel.lstrip('/')
        abspath = os.path.join(media_root, rel)
        if os.path.exists(abspath):
            found.append((u, abspath))
        else:
            missing.append((u, abspath))

print('MEDIA_ROOT:', media_root)
print('Found assets:', len(found))
for u, p in found[:50]:
    print('  ok ', u, '->', p)
print('Missing assets:', len(missing))
for u, p in missing[:200]:
    print('  missing', u, '->', p)

if missing:
    sys.exit(3)
else:
    sys.exit(0)
