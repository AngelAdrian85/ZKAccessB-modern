import ssl
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

u = "https://192.168.1.235/js/common.js"
req = urllib.request.Request(u, headers={"User-Agent": "zkprobe"})
with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
    data = r.read().decode("utf-8", "replace")

print('len', len(data))
for line in data.splitlines():
    if 'ajaxUrl' in line or 'https' in line or 'http' in line:
        if len(line) > 500:
            line = line[:500] + '...'
        print(line)
