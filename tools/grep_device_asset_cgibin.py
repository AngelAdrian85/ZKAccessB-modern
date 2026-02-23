import ssl
import sys
import urllib.request

BASE = 'https://192.168.1.235/'
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE

paths = sys.argv[1:] or ['js/main.js','left.html','net.html','header.html']
for p in paths:
    url = BASE + p.lstrip('/')
    req = urllib.request.Request(url, headers={'User-Agent':'zkprobe'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            data = r.read().decode('utf-8','replace')
    except Exception as e:
        print('\n==', p, 'FETCH FAILED', type(e).__name__, e)
        continue
    print('\n==', p, 'len', len(data))
    for line in data.splitlines():
        if '/cgi-bin/' in line:
            if len(line) > 700:
                line = line[:700] + '...'
            print(line)
