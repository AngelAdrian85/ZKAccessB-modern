from django.core.management.base import BaseCommand
from agent.models import DeviceStatus
import json

class Command(BaseCommand):
    help = 'Dump all DeviceStatus rows'

    def handle(self, *args, **options):
        qs = DeviceStatus.objects.select_related('device').order_by('device__id')
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
        self.stdout.write(json.dumps(out, indent=2, ensure_ascii=False))
