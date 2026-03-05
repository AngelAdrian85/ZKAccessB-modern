import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse

from agent.models import AuditLog, CommandLog, Device, DeviceRealtimeLog, Employee, EmployeeCard


@pytest.mark.django_db
def test_monitor_rtlog_polling_endpoint_requires_auth(client):
    url = reverse('api-monitor-rtlog')
    r = client.get(url)
    assert r.status_code == 403


@pytest.mark.django_db
def test_monitor_rtlog_polling_endpoint_returns_rows_after_id(client):
    u = User.objects.create_user('staffm', 'sm@b.c', 'pass')
    u.is_staff = True
    u.save()
    client.login(username='staffm', password='pass')

    a = DeviceRealtimeLog.objects.create(device_id=1, sn='SN1', raw='2026-02-19 10:00:00,0,123456,1,0,0')
    b = DeviceRealtimeLog.objects.create(device_id=1, sn='SN1', raw='2026-02-19 10:00:01,0,234567,1,0,0')

    url = reverse('api-monitor-rtlog')

    r0 = client.get(url)
    assert r0.status_code == 200
    j0 = r0.json()
    assert j0.get('ok') is True
    assert len(j0.get('rows') or []) >= 2

    r1 = client.get(url + f'?after_id={a.id}')
    assert r1.status_code == 200
    j1 = r1.json()
    assert j1.get('ok') is True
    rows1 = j1.get('rows') or []
    assert any(int(row.get('id')) == b.id for row in rows1)
    assert all(int(row.get('id')) > a.id for row in rows1)


@pytest.mark.django_db
def test_monitor_rtlog_polling_endpoint_includes_audit_rows_incrementally(client):
    u = User.objects.create_user('staff2', 's2@b.c', 'pass')
    u.is_staff = True
    u.save()
    client.login(username='staff2', password='pass')

    # Create at least one RTLOG row so endpoint is exercised normally.
    DeviceRealtimeLog.objects.create(device_id=1, sn='SN1', raw='2026-02-19 10:00:00,0,123456,1,0,0')

    a1 = AuditLog.objects.create(
        module='door',
        action='open',
        entity_id=10,
        entity_name='Door 10',
        user=None,
        ip_address=None,
        details='{"door_id":10,"device_id":1,"event_description":"door.open","status_text":"OK","verify_mode":"API"}',
    )

    url = reverse('api-monitor-rtlog')

    r0 = client.get(url)
    assert r0.status_code == 200
    j0 = r0.json()
    assert j0.get('ok') is True
    audit0 = j0.get('audit_rows') or []
    assert any(int(row.get('id')) == a1.id for row in audit0)
    assert isinstance(j0.get('last_audit_id'), int)

    r1 = client.get(url + f'?after_audit_id={a1.id}')
    assert r1.status_code == 200
    j1 = r1.json()
    assert j1.get('ok') is True
    audit1 = j1.get('audit_rows') or []
    assert all(int(row.get('id')) > a1.id for row in audit1)


@pytest.mark.django_db
def test_card_reader_push_normalizes_and_persists_for_monitor(client):
    # card_read_push itself is intentionally unauthenticated (local integrations)
    push_url = reverse('api-card-read-push')

    before = DeviceRealtimeLog.objects.count()
    r = client.post(
        push_url,
        data={
            'card_number': '04 ab:cd-12\r\n',
            'source': 'elatec',
        },
        content_type='application/json',
    )
    assert r.status_code == 200
    assert r.json().get('ok') is True

    assert DeviceRealtimeLog.objects.count() == before + 1
    last = DeviceRealtimeLog.objects.order_by('-id').first()
    assert last is not None
    # Must contain normalized card code; hex-like payloads are decoded to numeric.
    assert ',412,' in (last.raw or '')


@pytest.mark.django_db
def test_card_read_wait_can_read_from_controller_rtlog_rows(client):
    # Ensure we don't short-circuit due to a previous test run.
    cache.delete('agent:last_card_read')
    cache.delete('agent:last_card_read_rtlog_id')

    # Format A: ts,pin,card,door,code,verify,...
    DeviceRealtimeLog.objects.create(device_id=22, sn='SN22', raw='2026-02-19 10:00:00,0,12345678,1,0,0')

    url = reverse('api-card-read-wait')
    r = client.get(url)
    assert r.status_code == 200
    j = r.json()
    assert j.get('ok') is True
    assert j.get('card_number') == '12345678'
    assert j.get('source') == 'controller_rtlog'


@pytest.mark.django_db
def test_health_includes_monitor_integrity_diagnostics(client):
    dev = Device.objects.create(
        name='HEALTH_DEV',
        serial_number='SN_HEALTH_1',
        ip_address='192.168.1.220',
        port=4370,
        enabled=True,
    )
    CommandLog.objects.create(device=dev, command='SYNC_ALL', status='OK', result='synced')
    CommandLog.objects.create(device=dev, command='CLEAR_DEVICE_DATA', status='ERR', result='user:noeffect')
    DeviceRealtimeLog.objects.create(device_id=22, sn='SN22', raw='0,4,1,27,0,840045753,255,,0')
    DeviceRealtimeLog.objects.create(device_id=22, sn='SN22', raw='0,4,1,27,0,840045754,256,,0')

    r = client.get(reverse('agent-health'))
    assert r.status_code == 200
    j = r.json()
    assert j.get('ok') is True
    mi = j.get('monitor_integrity') or {}
    assert 'sync' in mi
    assert 'clear' in mi
    assert 'events' in mi
    assert int((mi.get('events') or {}).get('tx_rows_recent') or 0) >= 2


@pytest.mark.django_db
def test_system_normalize_cards_endpoint_normalizes_employee_and_employeecard(client):
    u = User.objects.create_user('staff_norm', 'norm@b.c', 'pass')
    u.is_staff = True
    u.save()
    client.login(username='staff_norm', password='pass')

    emp = Employee.objects.create(
        first_name='Card',
        last_name='Normalize',
        card_number='04 ab:cd-12',
        secondary_card_number='0x00-ff-aa',
        active=True,
    )
    ec = EmployeeCard.objects.create(employee=emp, card_number='  11 22-33  ')

    url = reverse('api-system-normalize-cards')
    r = client.post(url)
    assert r.status_code == 200
    body = r.json()
    assert body.get('ok') is True
    assert int(body.get('employees_changed') or 0) >= 1
    assert int(body.get('employee_cards_changed') or 0) >= 1

    emp.refresh_from_db()
    ec.refresh_from_db()
    assert emp.card_number == '04ABCD12'
    assert emp.secondary_card_number == '00FFAA'
    assert ec.card_number == '112233'
