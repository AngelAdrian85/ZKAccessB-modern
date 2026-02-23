import re
import ssl
import sys
import urllib.request

BASE = 'https://192.168.1.235/'
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE

path = sys.argv[1] if len(sys.argv) > 1 else 'left.html'
url = BASE + path.lstrip('/')
req = urllib.request.Request(url, headers={'User-Agent':'zkprobe'})
with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
    html = r.read().decode('utf-8','replace')

print('len', len(html))
links = []
for m in re.finditer(r"href\s*=\s*['\"]([^'\"]+)['\"]", html, flags=re.IGNORECASE):
    links.append(m.group(1).strip())
for m in re.finditer(r"src\s*=\s*['\"]([^'\"]+)['\"]", html, flags=re.IGNORECASE):
    links.append(m.group(1).strip())
uniq=[]; seen=set()
for l in links:
    if not l or l.startswith('#'):
        continue
    if l in seen:
        continue
    seen.add(l)
    uniq.append(l)
print('refs', len(uniq))
for l in uniq:
    print(l)
