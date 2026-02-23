import re
import ssl
import urllib.request

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
u = 'https://192.168.1.235/login.html'
req = urllib.request.Request(u, headers={'User-Agent':'zkprobe'})
with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
    html = r.read().decode('utf-8','replace')
print('len', len(html))
# Print input fields
for m in re.finditer(r"<input[^>]+>", html, flags=re.IGNORECASE):
    tag = m.group(0)
    if len(tag) > 220:
        tag = tag[:220] + '...'
    print(tag)
# Also show any occurrences of token-like strings
for key in ('token', 'csrf', 'session', 'sid', 'challenge', 'nonce'):
    if key in html.lower():
        print('contains', key)
