from django.test import Client
from django.contrib.auth import get_user_model
from agent.models import DeviceStatus

User = get_user_model()
user = User.objects.filter(is_superuser=True).first()
client = Client()
if user:
    client.force_login(user)

before = list(DeviceStatus.objects.values('device_id','updated_at'))
resp = client.get('/agent/')
print('STATUS', resp.status_code)
after = list(DeviceStatus.objects.values('device_id','updated_at'))
print('BEFORE')
for r in before:
    print(r)
print('AFTER')
for r in after:
    print(r)
