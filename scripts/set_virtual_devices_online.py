import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
HERE = Path(__file__).resolve().parent
ROOT = str(HERE.parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# Ensure the `zkeco_modern` package directory is on sys.path so the 'agent' app is importable
ZKMOD = os.path.join(ROOT, 'zkeco_modern')
if ZKMOD not in sys.path:
    sys.path.insert(0, ZKMOD)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')

import django
django.setup()

from django.apps import apps

Device = apps.get_model('agent', 'Device')
DeviceStatus = apps.get_model('agent', 'DeviceStatus')
from django.utils import timezone

acp_q = Device.objects.filter(scanner_type='acp', scanner_linked=True)
el_q = Device.objects.filter(scanner_type='elatec', scanner_linked=True)

acp_count = DeviceStatus.objects.filter(device__in=acp_q).update(online=True, updated_at=timezone.now())
el_count = DeviceStatus.objects.filter(device__in=el_q).update(online=True, updated_at=timezone.now())

print('ACP DeviceStatus rows updated:', acp_count)
print('Elatec DeviceStatus rows updated:', el_count)
