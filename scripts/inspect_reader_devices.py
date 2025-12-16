import os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = str(HERE.parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
ZKMOD = os.path.join(ROOT, 'zkeco_modern')
if ZKMOD not in sys.path:
    sys.path.insert(0, ZKMOD)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
import django
django.setup()
from django.apps import apps
Device = apps.get_model('agent', 'Device')
DeviceStatus = apps.get_model('agent', 'DeviceStatus')

q = Device.objects.filter(scanner_linked=True)
print('Linked devices count:', q.count())
for d in q:
    print('Device:', d.id, d.name, 'type=', d.scanner_type, 'enabled=', d.enabled)
    try:
        st = DeviceStatus.objects.filter(device=d).order_by('-updated_at').first()
        if st:
            print('  Status:', 'online=', st.online, 'updated_at=', st.updated_at)
        else:
            print('  Status: NONE')
    except Exception as e:
        print('  Status query error:', e)
