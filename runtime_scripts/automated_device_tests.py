from django.utils import timezone
import time, os, json
from agent.models import DeviceStatus
from agent.modern_comm_center import build_and_run_stub
import django

BASE = __import__('django.conf').conf.settings.BASE_DIR
RT_FILE = os.path.join(BASE, 'zkeco_modern', 'runtime_logs', 'last_status_broadcasts.json')

def snapshot_db():
    out = {}
    for d in DeviceStatus.objects.all():
        out[d.device_id] = {'updated_at': d.updated_at.isoformat() if d.updated_at else None, 'online': d.online}
    return out

print('DEVICES:', list(DeviceStatus.objects.values_list('device_id', flat=True)))
# Prepare: set all devices offline with old timestamp
old = timezone.now() - timezone.timedelta(days=1)
for d in DeviceStatus.objects.all():
    d.online = False
    d.updated_at = old
    d.save(update_fields=['online','updated_at'])
print('Prepared DB snapshot (old timestamps)')
print(snapshot_db())

# Remove runtime file
if os.path.exists(RT_FILE):
    try:
        os.remove(RT_FILE)
    except Exception:
        pass

# 1) Start commcenter with driver='socket' (likely to fail connecting) -> should NOT change DB
center = build_and_run_stub(poll_interval=0.5, driver='socket')
print('Started center with socket driver (no activity expected)')
time.sleep(1.5)
# capture runtime file and db
rt_exists = os.path.exists(RT_FILE)
rt_content = None
if rt_exists:
    try:
        rt_content = json.load(open(RT_FILE))
    except Exception:
        rt_content = None
print('RT FILE exists:', rt_exists)
print('RT CONTENT:', rt_content)
print('DB after socket start:', snapshot_db())
# stop
center._stop.set()

# 2) Start commcenter with driver='stub' (will return activity) -> should update DB
if os.path.exists(RT_FILE):
    try:
        os.remove(RT_FILE)
    except Exception:
        pass
center = build_and_run_stub(poll_interval=0.5, driver='stub')
print('Started center with stub driver (activity expected)')
time.sleep(1.5)
rt_exists = os.path.exists(RT_FILE)
rt_content = None
if rt_exists:
    try:
        rt_content = json.load(open(RT_FILE))
    except Exception:
        rt_content = None
print('RT FILE exists after stub:', rt_exists)
print('RT CONTENT after stub:', rt_content)
print('DB after stub start:', snapshot_db())
center._stop.set()
