from django.utils import timezone
import os, time, json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.apps import apps

BASE = __import__('django.conf').conf.settings.BASE_DIR
RT_FILE = os.path.join(BASE, 'zkeco_modern', 'runtime_logs', 'last_status_broadcasts.json')

DeviceStatus = apps.get_model('agent', 'DeviceStatus')

def snapshot_db():
    out = {}
    for d in DeviceStatus.objects.all():
        out[d.device_id] = {'updated_at': d.updated_at.isoformat() if d.updated_at else None, 'online': d.online}
    return out

print('Initial DB snapshot:')
print(snapshot_db())
print('Initial RT exists:', os.path.exists(RT_FILE))
if os.path.exists(RT_FILE):
    print('Initial RT content:', json.load(open(RT_FILE)))

# Start center (stub)
from agent.modern_comm_center import build_and_run_stub
center = build_and_run_stub(poll_interval=0.5, driver='stub')
print('Started stub center')
# wait for broadcast
time.sleep(1.0)
print('After start RT exists:', os.path.exists(RT_FILE))
if os.path.exists(RT_FILE):
    print('RT content after start:', json.load(open(RT_FILE)))
print('DB after start:', snapshot_db())

# Simulate stopping a device's service: toggle device 1 offline via DB
print('Simulating service stop for device 1 (set offline)')
d = DeviceStatus.objects.filter(device_id=1).first()
if d:
    d.online = False
    d.updated_at = timezone.now()
    d.save(update_fields=['online','updated_at'])
print('DB after manual stop:', snapshot_db())

# Simulate page refresh: call MonitorConsumer._fetch_status_map
try:
    from agent.consumers import MonitorConsumer
    mc = MonitorConsumer()
    # _fetch_status_map is database_sync_to_async; call via async_to_sync
    from asgiref.sync import async_to_sync
    status_map = async_to_sync(mc._fetch_status_map)()
    print('MonitorConsumer._fetch_status_map ->', status_map)
except Exception as e:
    print('MonitorConsumer fetch failed:', e)

# Now simulate full restart: stop center thread and start a fresh one
center._stop.set()
print('Stopped center; waiting 0.5s')
time.sleep(0.5)
center2 = build_and_run_stub(poll_interval=0.5, driver='stub')
print('Started new center (simulating tray restart)')
# wait
time.sleep(1.0)
print('RT after restart exists:', os.path.exists(RT_FILE))
if os.path.exists(RT_FILE):
    print('RT content after restart:', json.load(open(RT_FILE)))
print('DB after restart:', snapshot_db())

# Simulate page-render device_statuses building (same logic as access_dashboard view)
print('\nSimulated access_dashboard device_statuses:')
try:
    broadcasts = json.load(open(RT_FILE)) if os.path.exists(RT_FILE) else {}
except Exception:
    broadcasts = {}
device_statuses = []
for ds_obj in DeviceStatus.objects.select_related('device').all():
    dev = getattr(ds_obj, 'device', None)
    ua_iso = None
    try:
        dev_id_key = str(getattr(dev, 'id', None) or getattr(ds_obj, 'device_id', None))
        if dev_id_key and dev_id_key in broadcasts and broadcasts.get(dev_id_key):
            ua_iso = broadcasts.get(dev_id_key)
        else:
            ua_iso = ds_obj.updated_at.isoformat() if ds_obj.updated_at is not None else None
    except Exception:
        ua_iso = None
    device_statuses.append({'device_id': getattr(dev, 'id', None), 'online': ds_obj.online, 'updated_at': ua_iso})
print(device_statuses)

# cleanup
center2._stop.set()
print('Finished simulation')
