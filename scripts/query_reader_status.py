import os,sys,json
BASE = os.path.dirname(os.path.dirname(__file__))
# Ensure modern project directory is on path (same as manage.py)
modern_dir = os.path.join(BASE, 'zkeco_modern')
if modern_dir not in sys.path:
    sys.path.insert(0, modern_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE','zkeco_config.settings')
import django
django.setup()
from zkeco_modern.agent.models import DeviceStatus
qs = DeviceStatus.objects.select_related('device').filter(device__device_type__icontains('reader')).order_by('device__name')
out = []
for ds in qs:
    dev = getattr(ds, 'device', None)
    out.append({
        'device_id': getattr(dev, 'id', None),
        'device_name': getattr(dev, 'name', None),
        'serial': getattr(dev, 'serial_number', None),
        'online': ds.online,
        'door_state': ds.door_state,
        'updated_at': ds.updated_at.isoformat() if ds.updated_at else None,
    })
print(json.dumps(out, indent=2, ensure_ascii=False))
