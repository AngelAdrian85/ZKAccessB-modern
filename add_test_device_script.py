import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_modern.settings')
if os.path.exists(os.path.join(os.path.dirname(__file__), 'zkeco_modern')):
    sys.path.insert(0, os.path.dirname(__file__))

django.setup()

# Now we can import models
from zkeco_modern.agent.models import Device
from django.utils import timezone

try:
    # Check if test device exists
    if not Device.objects.filter(serial_number='TEST_DEVICE_001').exists():
        device = Device.objects.create(
            name='Test Access Panel',
            serial_number='TEST_DEVICE_001',
            device_type='access_panel',
            comm_mode='tcp',
            ip_address='192.168.1.100',
            port=4370,
            comm_password='',
            area_name='Test Area',
            time_zone='UTC+2',
            enabled=True,
            auto_sync_time=True,
            clear_on_add=False,
            firmware_version='V1.0.0',
            hardware_version='ZK',
            last_contact=timezone.now()
        )
        print(f'✓ Test device created: {device.name} (SN: {device.serial_number})')
    else:
        print('ℹ Test device already exists')

    # List all devices
    devices = Device.objects.all()
    print(f'\nTotal devices in database: {devices.count()}')
    for d in devices:
        print(f'  - {d.name} ({d.serial_number})')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()

