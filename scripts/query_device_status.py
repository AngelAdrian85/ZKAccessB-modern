from agent.models import Device, DeviceStatus
print('DEVICES:', list(Device.objects.values('id','name','scanner_type')))
print('STATUS:', list(DeviceStatus.objects.values('device_id','online','updated_at')))
