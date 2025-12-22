import json, os
from agent.models import DeviceStatus
from django.conf import settings

def snapshot_db():
    out=[]
    for d in DeviceStatus.objects.all():
        out.append({'device_id': d.device_id, 'updated_at': d.updated_at.isoformat() if d.updated_at else None, 'online': d.online})
    return out

print(json.dumps({'db': snapshot_db()}, indent=2))
base = getattr(settings, 'BASE_DIR', os.getcwd())
rt = os.path.join(base, 'zkeco_modern', 'runtime_logs', 'last_status_broadcasts.json')
print('RT_EXISTS', os.path.exists(rt))
if os.path.exists(rt):
    try:
        print(json.dumps(json.load(open(rt, 'r', encoding='utf-8')), indent=2))
    except Exception as e:
        print('RT_READ_ERR', e)
else:
    print('NO_RT')
logp = os.path.join(base, 'zkeco_modern', 'logs', 'tray_agent.log')
if os.path.exists(logp):
    print('\n---TAIL LOG---')
    try:
        txt = open(logp, 'r', encoding='utf-8', errors='replace').read()
        print(txt[-2000:])
    except Exception as e:
        print('LOG_READ_ERR', e)
else:
    print('NO_LOG')
