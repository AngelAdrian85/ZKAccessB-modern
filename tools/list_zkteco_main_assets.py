import re
import ssl
import urllib.request

BASE = 'https://192.168.1.235/'
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE

u = BASE + 'main.html'
req = urllib.request.Request(u, headers={'User-Agent':'zkprobe'})
with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
    html = r.read().decode('utf-8','replace')

print('len', len(html))
# crude extraction of src/href
links = []
for m in re.finditer(r"(?:src|href)\s*=\s*['\"]([^'\"]+)['\"]", html, flags=re.IGNORECASE):
    val = m.group(1).strip()
    if not val:
        continue
    links.append(val)

# also look for iframe/frame
for m in re.finditer(r"<(?:frame|iframe)[^>]+src\s*=\s*['\"]([^'\"]+)['\"]", html, flags=re.IGNORECASE):
    links.append(m.group(1).strip())

uniq = []
seen = set()
for l in links:
    if l in seen:
        continue
    seen.add(l)
    uniq.append(l)

print('assets', len(uniq))
for l in uniq:
    print(l)
