import datetime

import pytest
from django.contrib.auth.models import User

from agent.models import CommandLog, Device, DeviceStatus, Door, TimeSegment


@pytest.mark.django_db
def test_generic_open_close_use_pulse_commands_when_not_normally_open(client):
    u = User.objects.create_user('staff_door_mode1', 'm1@b.c', 'pass')
    u.is_staff = True
    u.is_superuser = True
    u.save()
    assert client.login(username='staff_door_mode1', password='pass')

    dev = Device.objects.create(
        name='CTRL_MODE_1',
        serial_number='SN_MODE_1',
        ip_address='192.168.55.11',
        port=4370,
        enabled=True,
    )
    DeviceStatus.objects.create(device=dev, online=True, door_state='CLOSED')

    seg = TimeSegment.objects.create(
        name='SEG_MODE_1',
        start_time=datetime.time(0, 0, 0),
        end_time=datetime.time(23, 59, 59),
        days_mask=127,
    )
    door = Door.objects.create(
        name='D1',
        device=dev,
        door_number=1,
        normally_open=False,
        door_active_time_zone=seg,
    )

    r_open = client.get(f'/agent/api/devices/{dev.id}/doors/{door.id}/open/')
    assert r_open.status_code == 200
    j_open = r_open.json()
    assert j_open.get('ok') is True
    assert j_open.get('mode') == 'pulse'
    assert j_open.get('command') == 'DOOR_OPEN'

    r_close = client.get(f'/agent/api/devices/{dev.id}/doors/{door.id}/close/')
    assert r_close.status_code == 200
    j_close = r_close.json()
    assert j_close.get('ok') is True
    assert j_close.get('mode') == 'pulse'
    assert j_close.get('command') == 'DOOR_CLOSE'

    cmds = list(CommandLog.objects.filter(device=dev).order_by('id').values_list('command', flat=True))
    assert 'DOOR_OPEN:1' in cmds
    assert 'DOOR_CLOSE:1' in cmds


@pytest.mark.django_db
def test_generic_open_close_use_normal_commands_when_normally_open(client):
    u = User.objects.create_user('staff_door_mode2', 'm2@b.c', 'pass')
    u.is_staff = True
    u.is_superuser = True
    u.save()
    assert client.login(username='staff_door_mode2', password='pass')

    dev = Device.objects.create(
        name='CTRL_MODE_2',
        serial_number='SN_MODE_2',
        ip_address='192.168.55.12',
        port=4370,
        enabled=True,
    )
    DeviceStatus.objects.create(device=dev, online=True, door_state='CLOSED')

    seg = TimeSegment.objects.create(
        name='SEG_MODE_2',
        start_time=datetime.time(0, 0, 0),
        end_time=datetime.time(23, 59, 59),
        days_mask=127,
    )
    door = Door.objects.create(
        name='D1',
        device=dev,
        door_number=1,
        normally_open=True,
        door_active_time_zone=seg,
    )

    r_open = client.get(f'/agent/api/devices/{dev.id}/doors/{door.id}/open/')
    assert r_open.status_code == 200
    j_open = r_open.json()
    assert j_open.get('ok') is True
    assert j_open.get('mode') == 'normal'
    assert j_open.get('command') == 'DOOR_NORMAL_OPEN'

    r_close = client.get(f'/agent/api/devices/{dev.id}/doors/{door.id}/close/')
    assert r_close.status_code == 200
    j_close = r_close.json()
    assert j_close.get('ok') is True
    assert j_close.get('mode') == 'normal'
    assert j_close.get('command') == 'DOOR_NORMAL_CLOSE'

    cmds = list(CommandLog.objects.filter(device=dev).order_by('id').values_list('command', flat=True))
    assert 'DOOR_NORMAL_OPEN:1' in cmds
    assert 'DOOR_NORMAL_CLOSE:1' in cmds
