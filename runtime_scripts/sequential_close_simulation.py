from django.utils import timezone
import os, time, json
from django.apps import apps

BASE = __import__('django.conf').conf.settings.BASE_DIR
RT_FILE = os.path.join(BASE, 'zkeco_modern', 'runtime_logs', 'last_status_broadcasts.json')
DeviceStatus = apps.get_model('agent', 'DeviceStatus')

def snapshot_db():
    out = {}
    for d in DeviceStatus.objects.all():
        out[d.device_id] = {'updated_at': d.updated_at.isoformat() if d.updated_at else None, 'online': d.online}
    return out

print('Initial DB:', snapshot_db())
print('Initial RT exists:', os.path.exists(RT_FILE))
if os.path.exists(RT_FILE):
    print('Initial RT content:', json.load(open(RT_FILE)))

# Sequentially stop devices 1,2,3 and simulate a client refresh after each stop
for did in [1,2,3]:
    print('\n-- Stopping device', did)
    ds = DeviceStatus.objects.filter(device_id=did).first()
    if ds:
        ds.online = False
        ds.updated_at = timezone.now()
        ds.save(update_fields=['online','updated_at'])
        # Broadcast status (so WebSocket clients see it); this does NOT write RT file
        try:
            from agent.ws import broadcast_device_status
            ua = ds.updated_at.isoformat() if ds.updated_at else None
            broadcast_device_status(did, False, updated_at=ua)
        except Exception:
            pass
    time.sleep(0.5)
    # Simulate page refresh (access_dashboard logic): prefer most recent between DB and RT file
    try:
        broadcasts = json.load(open(RT_FILE)) if os.path.exists(RT_FILE) else {}
    except Exception:
        broadcasts = {}
    device_statuses = []
    for ds_obj in DeviceStatus.objects.select_related('device').all():
        ua_iso = None
        try:
            dev_id_key = str(getattr(ds_obj, 'device_id', None))
            b = broadcasts.get(dev_id_key)
            from django.utils.dateparse import parse_datetime
            from django.utils import timezone as dj_tz
            db_ts = ds_obj.updated_at if getattr(ds_obj, 'updated_at', None) is not None else None
            b_ts = None
            if b:
                try:
                    b_ts = parse_datetime(b)
                    if b_ts is not None and dj_tz.is_naive(b_ts):
                        b_ts = dj_tz.make_aware(b_ts, dj_tz.get_current_timezone())
                except Exception:
                    b_ts = None
            chosen = None
            if db_ts and b_ts:
                try:
                    chosen = db_ts if db_ts >= b_ts else b_ts
                except Exception:
                    chosen = db_ts or b_ts
            else:
                chosen = db_ts or b_ts
            if chosen is not None:
                ua_iso = chosen.isoformat() if hasattr(chosen, 'isoformat') else str(chosen)
        except Exception:
            ua_iso = None
        device_statuses.append({'device_id': ds_obj.device_id, 'online': ds_obj.online, 'updated_at': ua_iso})
    print('After stopping', did, 'DB snapshot:', snapshot_db())
    print('After stopping', did, 'simulated page device_statuses:', device_statuses)
    time.sleep(0.5)

print('\nFinished sequential stop simulation')
