#!/usr/bin/env python3
import requests, json
from pathlib import Path
rp = Path(__file__).resolve().parent
rendered = rp / 'rendered_pages'
out = rp.parent / 'reports' / 'legacy_render_check.json'
out.parent.mkdir(parents=True, exist_ok=True)
results = {}
if not rendered.exists():
    print('No rendered pages dir')
    raise SystemExit(1)
files = sorted([p for p in rendered.glob('*.html')])
for f in files:
    name = f.name
    url = f'http://127.0.0.1:8000/legacy/{name}'
    try:
        r = requests.get(url, timeout=8)
        results[name] = {'url': url, 'status': r.status_code, 'len': len(r.content)}
    except Exception as e:
        results[name] = {'url': url, 'error': str(e)}
out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
print('WROTE', out)
