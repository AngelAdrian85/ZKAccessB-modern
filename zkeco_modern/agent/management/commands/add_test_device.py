from django.core.management.base import BaseCommand
from agent.models import Device
from django.utils import timezone


class Command(BaseCommand):
    help = 'Add a test device to the database'

    def handle(self, *args, **options):
        # Check if test device already exists
        if Device.objects.filter(serial_number='TEST_DEVICE_001').exists():
            self.stdout.write(self.style.WARNING('Test device already exists'))
            return

        # Create test device
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

        self.stdout.write(self.style.SUCCESS(f'Test device created: {device.name} (SN: {device.serial_number})'))
