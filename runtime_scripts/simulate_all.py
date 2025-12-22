from django.utils import timezone
from agent.models import DeviceStatus
from agent.ws import broadcast_device_status

qs = list(DeviceStatus.objects.all())
print('SIMULATE COUNT', len(qs))
for obj in qs:
    # offline
    obj.online = False
    obj.updated_at = timezone.now()
    obj.save()
    try:
        broadcast_device_status(obj.device_id, False, serial=getattr(obj, 'serial', ''), updated_at=obj.updated_at.isoformat())
    except Exception:
        pass

for obj in qs:
    # online
    obj.online = True
    obj.updated_at = timezone.now()
    obj.save()
    try:
        broadcast_device_status(obj.device_id, True, serial=getattr(obj, 'serial', ''), updated_at=obj.updated_at.isoformat())
    except Exception:
        pass

print('SIMULATION DONE')
