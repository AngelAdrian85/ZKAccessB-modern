import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import time


@pytest.mark.django_db
def test_access_level_unique_by_time_segment_and_doors_and_queues_sync(client):
    # Staff user
    u = User.objects.create_user('staff_al', 'al@b.c', 'pass')
    u.is_staff = True
    u.save()
    client.login(username='staff_al', password='pass')

    from agent.models import Device, Door, TimeSegment, AccessLevel, CommandLog

    dev = Device.objects.create(
        name='Centrală Test AL',
        serial_number='SN_AL_001',
        device_type='access_panel',
        comm_mode='tcp',
        ip_address='192.168.1.200',
        port=4370,
        enabled=True,
    )

    # Doors on controller (door-set is derived from selected controllers)
    Door.objects.create(device=dev, door_number=1, name='Ușă A', enabled=True)
    Door.objects.create(device=dev, door_number=2, name='Ușă B', enabled=True)

    ts = TimeSegment.objects.create(name='TS Test', start_time=time(0, 0), end_time=time(23, 59))

    url = reverse('crud-access-level-create')

    # Create access level
    r1 = client.post(
        url,
        {
            'name': 'Nivel Test 1',
            'description': 'desc',
            'time_segment': str(ts.id),
            'is_visitor': '0',
            'devices': [str(dev.id)],
        },
    )
    assert r1.status_code == 200
    assert AccessLevel.objects.count() == 1

    al1 = AccessLevel.objects.first()
    assert al1 is not None
    assert al1.signature, 'signature must be computed to enforce uniqueness'

    # Sync should be queued for the affected controller (signals or view enqueue)
    assert CommandLog.objects.filter(device_id=dev.id, command__startswith='SYNC_PERSONNEL').exists()

    # Attempt to create another level with same time segment + same controller -> same derived doors -> must fail
    r2 = client.post(
        url,
        {
            'name': 'Nivel Test 2',
            'description': 'desc2',
            'time_segment': str(ts.id),
            'is_visitor': '0',
            'devices': [str(dev.id)],
        },
    )
    assert r2.status_code == 200
    assert AccessLevel.objects.count() == 1, 'should reject duplicate (time segment + door set)'
