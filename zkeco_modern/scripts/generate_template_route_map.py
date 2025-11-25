#!/usr/bin/env python3
import json
from pathlib import Path
rp = Path(__file__).resolve().parent
rendered = rp / 'rendered_pages'
out = rp.parent / 'reports' / 'template_route_map.json'
map_data = {}
if rendered.exists():
    for f in rendered.glob('*.html'):
        name = f.stem
        candidates = []
        # direct basename
        candidates.append('/' + name)
        # lowercase
        candidates.append('/' + name.lower())
        # path variant where double-underscore means a slash
        candidates.append('/' + name.replace('__','/'))
        candidates.append('/' + name.replace('__','/').lower())
        # filename as-is
        candidates.append('/' + f.name)
        # root mapping for index-like files
        if name.lower() in ('index','home','default'):
            candidates.insert(0, '/')
        # unique
        candidates = [c for i,c in enumerate(candidates) if c not in candidates[:i]]
        map_data[f.name] = candidates
else:
    print('No rendered_pages found')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(map_data, indent=2, ensure_ascii=False))
print('WROTE', out)
