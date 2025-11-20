#!/usr/bin/env python3
import json
from pathlib import Path
rp = Path(__file__).resolve().parent
mapf = rp.parent / 'reports' / 'template_route_map.json'
out = rp.parent / 'reports' / 'curated_template_mapping.json'
priority_keywords = ['index','user','user_list','user_edit','data_list','view','view_detail','registration','login','upload','import','export','setoption','sys_option','transaction','upgrade']

if not mapf.exists():
    print('missing template_route_map.json')
    raise SystemExit(1)
map_data = json.loads(mapf.read_text())
curated = {}
for tmpl, cand in map_data.items():
    key = tmpl.lower()
    for kw in priority_keywords:
        if kw in key:
            curated[tmpl] = cand
            break
# Always include registration templates if present
for t in list(map_data.keys()):
    if t.startswith('registration'):
        curated[t] = map_data[t]

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(curated, indent=2, ensure_ascii=False))
print('WROTE', out)
