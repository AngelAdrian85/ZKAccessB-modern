#!/usr/bin/env python3
import urllib.request
import sys

urls = [
    'http://127.0.0.1:8000/',
    'http://127.0.0.1:8000/registration/login/'
]
ok = True
for u in urls:
    try:
        r = urllib.request.urlopen(u, timeout=5)
        data = r.read(8192)
        print(f"{u} -> {r.getcode()} ({len(data)} bytes)")
        snippet = data.decode('utf-8', errors='replace')
        print(snippet[:500])
        print('---')
        if r.getcode() != 200:
            ok = False
    except Exception as e:
        print(f"{u} -> ERROR: {e}")
        ok = False

if not ok:
    sys.exit(2)
print('ALL_PAGES_OK')
