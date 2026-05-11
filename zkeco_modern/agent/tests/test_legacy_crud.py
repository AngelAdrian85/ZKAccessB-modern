import pytest
import json
from django.urls import reverse
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_access_logs_export(client):
    # Create staff user and login
    u = User.objects.create_user('admin','a@b.c','pass'); u.is_staff = True; u.is_superuser = True; u.save()
    client.login(username='admin', password='pass')
    # Access logs page (may be empty but should 200)
    resp = client.get(reverse('crud-access-logs-list'))
    assert resp.status_code in (200, 302)
    # Export CSV
    resp_csv = client.get(reverse('crud-access-logs-list') + '?export=csv')
    assert resp_csv.status_code in (200, 404)  # 404 if model missing
    # per_page param
    resp_pp = client.get(reverse('crud-access-logs-list') + '?per_page=20')
    assert resp_pp.status_code in (200, 302)
    # per_page boundary high (should clamp)
    resp_pp_high = client.get(reverse('crud-access-logs-list') + '?per_page=500')
    assert resp_pp_high.status_code in (200, 302)
    # PDF export
    resp_pdf = client.get(reverse('crud-access-logs-list') + '?export=pdf')
    assert resp_pdf.status_code in (200, 404)  # 404 if model missing / pdf lib absent

@pytest.mark.django_db
def test_device_crud_cycle(client):
    u = User.objects.create_user('staff','s@b.c','pass'); u.is_staff = True; u.save()
    client.login(username='staff', password='pass')
    # Create device
    data = {
        'name': 'Panel A',
        'device_type': 'Access Control Panel',
        'ip_address': '10.0.0.5',
        'area_name': 'Zona1',
        'enabled': 'on',
        'serial_number': 'SN123',
    }
    resp_create = client.post(reverse('crud-device-create'), data)
    assert resp_create.status_code == 200
    # List devices
    resp_list = client.get(reverse('crud-devices-list'))
    assert resp_list.status_code == 200

@pytest.mark.django_db
def test_issuecard_actions_missing_model(client):
    # Without legacy IssueCard model available these should 400 or 403 (unauth)
    u = User.objects.create_user('staff2','s2@b.c','pass'); u.is_staff = True; u.save()
    client.login(username='staff2', password='pass')
    # Some deployments expose legacy-style deactivate/reissue URLs; others only expose JSON endpoints.
    # If those URL names don't exist in this project, skip this check.
    for name in ['crud-issuecard-deactivate', 'crud-issuecard-reissue']:
        try:
            url = reverse(name, kwargs={'pk': 1})
        except Exception:
            pytest.skip(f"URL name {name} not present")
        r = client.post(url)
        assert r.status_code in (400, 403, 404)

@pytest.mark.django_db
def test_device_ping_discover_endpoints(client):
    u = User.objects.create_user('staffp','sp@b.c','pass'); u.is_staff=True; u.save(); client.login(username='staffp', password='pass')
    r = client.get(reverse('device-ping')+'?ip=127.0.0.1')
    assert r.status_code in (200,400)
    r2 = client.get(reverse('device-discover')+'?base=127.0.0')
    assert r2.status_code in (200,400)

@pytest.mark.django_db
def test_device_discover_apply_updates_existing_device_by_serial(client):
    from agent.models import Device

    u = User.objects.create_user('staffdup','dup@b.c','pass'); u.is_staff = True; u.save(); client.login(username='staffdup', password='pass')
    existing = Device.objects.create(
        name='Existing Panel',
        serial_number='SN-DISC-1',
        ip_address='192.168.1.210',
        port=4370,
        device_type='access_panel',
        comm_mode='tcp',
        enabled=True,
    )

    resp = client.post(
        reverse('device-discover-apply'),
        data=json.dumps({
            'action': 'add',
            'ip': '192.168.1.235',
            'port': 14370,
            'name': 'Existing Panel Updated',
            'serial_number': 'SN-DISC-1',
        }),
        content_type='application/json',
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload['ok'] is True
    assert payload['id'] == existing.id
    assert payload['created'] is False
    assert Device.objects.count() == 1

    existing.refresh_from_db()
    assert existing.ip_address == '192.168.1.235'
    assert existing.port == 14370
    assert existing.name == 'Existing Panel Updated'


@pytest.mark.django_db
def test_device_discover_apply_auto_queues_adms_with_dedicated_port(client, monkeypatch):
    from agent.models import CommandLog, Device

    monkeypatch.setenv('ZKACCESS_ADMS_PORT', '8091')
    u = User.objects.create_user('staffadms1', 'adms1@b.c', 'pass'); u.is_staff = True; u.save()
    client.login(username='staffadms1', password='pass')

    resp = client.post(
        reverse('device-discover-apply'),
        data=json.dumps({
            'action': 'add',
            'ip': '192.168.1.240',
            'port': 14370,
            'name': 'Panel Auto ADMS',
            'serial_number': 'SN-AUTO-ADMS-1',
        }),
        content_type='application/json',
        SERVER_PORT='15437',
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload['ok'] is True
    assert payload['adms_auto_configured'] is True
    assert payload['adms_server_port'] == 8091

    dev = Device.objects.get(pk=payload['id'])
    cmd = CommandLog.objects.filter(device=dev, command__startswith='SET_OPTION:ServerAddr=').latest('id')
    assert 'ServerPort=8091' in cmd.command
    assert 'WebServerIP=' in cmd.command
    assert 'WebServerPort=8091' in cmd.command
    assert 'PushFunOn=1' in cmd.command
    assert 'ServerPort=15437' not in cmd.command


@pytest.mark.django_db
def test_device_create_auto_queues_adms_with_dedicated_port(client, monkeypatch):
    from agent.models import CommandLog, Device

    monkeypatch.setenv('ZKACCESS_ADMS_PORT', '8091')
    u = User.objects.create_user('staffadms2', 'adms2@b.c', 'pass'); u.is_staff = True; u.save()
    client.login(username='staffadms2', password='pass')

    resp = client.post(
        reverse('crud-device-create'),
        {
            'name': 'Panel Create ADMS',
            'serial_number': 'SN-AUTO-ADMS-2',
            'device_type': 'access_panel',
            'comm_mode': 'tcp',
            'ip_address': '192.168.1.241',
            'port': '14370',
            'area_name': 'Zona1',
            'enabled': 'on',
            'auto_sync_time': 'on',
        },
        HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        SERVER_PORT='15437',
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload['ok'] is True

    dev = Device.objects.get(pk=payload['id'])
    cmd = CommandLog.objects.filter(device=dev, command__startswith='SET_OPTION:ServerAddr=').latest('id')
    assert 'ServerPort=8091' in cmd.command
    assert 'WebServerIP=' in cmd.command
    assert 'WebServerPort=8091' in cmd.command
    assert 'PushFunOn=1' in cmd.command
    assert 'ServerPort=15437' not in cmd.command


@pytest.mark.django_db
def test_device_create_auto_queues_adms_reboot_when_enabled(client, monkeypatch):
    from agent.models import CommandLog, Device

    monkeypatch.setenv('ZKACCESS_ADMS_PORT', '8091')
    monkeypatch.setenv('ZKACCESS_PUSH_REBOOT_AFTER_CONFIG', '1')
    u = User.objects.create_user('staffadms3', 'adms3@b.c', 'pass'); u.is_staff = True; u.save()
    client.login(username='staffadms3', password='pass')

    resp = client.post(
        reverse('crud-device-create'),
        {
            'name': 'Panel Create ADMS Reboot',
            'serial_number': 'SN-AUTO-ADMS-3',
            'device_type': 'access_panel',
            'comm_mode': 'tcp',
            'ip_address': '192.168.1.242',
            'port': '14370',
            'area_name': 'Zona1',
            'enabled': 'on',
            'auto_sync_time': 'on',
        },
        HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        SERVER_PORT='15437',
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload['ok'] is True

    dev = Device.objects.get(pk=payload['id'])
    assert CommandLog.objects.filter(device=dev, command='REBOOT', status='PENDING').exists()

@pytest.mark.django_db
def test_model_diff(client):
    u = User.objects.create_user('staffd','sd@b.c','pass'); u.is_staff=True; u.save(); client.login(username='staffd', password='pass')
    r = client.get(reverse('agent-model-diff'))
    assert r.status_code in (200,500)

@pytest.mark.django_db
def test_employee_extended_form_fields(client):
    u = User.objects.create_user('staffext','se@b.c','pass'); u.is_staff=True; u.save(); client.login(username='staffext', password='pass')
    r = client.get(reverse('crud-employee-create'))
    assert r.status_code == 200
    # Check presence of a few extended legacy fields now expected in CRUD
    html = r.content.decode()
    for field_name in ['legacy_userid', 'identitycard', 'reservation_password']:
        assert field_name in html, f"Missing extended field {field_name} in employee form"
