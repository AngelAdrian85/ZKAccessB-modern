import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from agent.models import DeviceRealtimeLog


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
