import pytest
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.mark.django_db
def test_wizard_device_create_requires_doors_then_creates(client):
    # Staff user
    u = User.objects.create_user('staff_wiz', 'wiz@b.c', 'pass')
    u.is_staff = True
    u.save()
    client.login(username='staff_wiz', password='pass')

    wizard_token = 'wz_test_123'

    # Open wizard form (GET)
    url = reverse('crud-device-create-access') + f'?wizard=1&wizard_token={wizard_token}'
    r = client.get(url)
    assert r.status_code == 200

    # Attempt to create without door drafts -> should not create in DB
    data = {
        'name': 'Centrală Test',
        'serial_number': '',
        'device_type': 'access_panel',
        'comm_mode': 'tcp',
        'ip_address': '192.168.1.250',
        'port': '14370',
        'comm_password': '',
        'rs485_port': 'COM1',
        'rs485_baudrate': '9600',
        'rs485_address': '',
        'area_name': 'Zona Test',
        'time_zone': '',
        'firmware_version': '',
        'hardware_version': '',  # keep empty so inferred capacity falls back to 1
        'enabled': 'on',
        'auto_sync_time': 'on',
        'clear_on_add': '',
        'scanner_linked': '',
        'scanner_type': '',
        'wizard_token': wizard_token,
    }

    from agent.models import Device

    assert Device.objects.count() == 0
    r2 = client.post(url, data)
    assert r2.status_code == 200
    assert Device.objects.count() == 0
    html = r2.content.decode('utf-8', errors='ignore')
    assert 'Configurează ușile' in html

    # Save door draft for door 1
    door_url = reverse('wizard-door-draft-edit', kwargs={'door_no': 1}) + f'?wizard_token={wizard_token}'
    r3 = client.post(
        door_url,
        {
            'door_number': '1',
            'name': 'Ușă 1',
            'reader_in_custom_name': 'Reader In',
            'reader_out_custom_name': 'Reader Out',
            'normally_open': 'on',
            'enabled': 'on',
            'wizard_token': wizard_token,
        },
    )
    assert r3.status_code == 200

    # Now create should succeed
    r4 = client.post(url, data)
    assert r4.status_code == 200
    assert Device.objects.count() == 1

    dev = Device.objects.first()
    assert dev is not None
    assert dev.ip_address == '192.168.1.250'
    assert dev.port == 14370
    assert dev.area_name == 'Zona Test'

    # Doors should be provisioned for controllers
    from agent.models import Door, DeviceStatus

    doors = list(Door.objects.filter(device=dev).order_by('door_number', 'id'))
    assert len(doors) >= 1
    assert doors[0].door_number == 1

    # A baseline status row should exist so device lists don't show OFFLINE on first render
    assert DeviceStatus.objects.filter(device=dev).exists()
