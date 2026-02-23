import ssl
import urllib.request

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
u = 'https://192.168.1.235/cgi-bin/param.cgi'
req = urllib.request.Request(u, headers={'User-Agent':'zkprobe'})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
        raw = r.read()
        print('status', getattr(r,'status',200))
        print(raw[:4000].decode('utf-8','replace'))
except Exception as e:
    print(type(e).__name__, e)
    if hasattr(e,'read'):
        try:
            print(e.read()[:4000].decode('utf-8','replace'))
        except Exception:
            pass
