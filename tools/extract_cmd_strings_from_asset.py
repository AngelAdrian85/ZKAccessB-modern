import re
import ssl
import sys
import urllib.request

BASE = 'https://192.168.1.235/'
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE

paths = sys.argv[1:]
if not paths:
    print('Usage: extract_cmd_strings_from_asset.py <path1> [path2...]')
    raise SystemExit(2)

cmd_re = re.compile(r"\"cmd\"\s*:\s*\"([^\"]+)\"")

for p in paths:
    url = BASE + p.lstrip('/')
    req = urllib.request.Request(url, headers={'User-Agent':'zkprobe'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            txt = r.read().decode('utf-8','replace')
    except Exception as e:
        print('\n==', p, 'FETCH FAILED', type(e).__name__, e)
        continue

    cmds = sorted(set(cmd_re.findall(txt)))
    print('\n==', p, 'cmds', len(cmds))
    for c in cmds:
        print(' ', c)
