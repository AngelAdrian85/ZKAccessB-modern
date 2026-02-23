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
    txt = r.read().decode('utf-8','replace')

htmls = sorted(set(re.findall(r"[a-zA-Z0-9_\-/]+\.html", txt)))
print('found', len(htmls), 'html strings in', path)
for h in htmls:
    print(' ', h)
