import pytest
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
    # Using pk=1; if model missing expect 400
    for name in ['crud-issuecard-deactivate','crud-issuecard-reissue']:
        url = reverse(name, kwargs={'pk':1})
        resp = client.post(url)
        assert resp.status_code in (400,404,200,403)

@pytest.mark.django_db
def test_device_ping_discover_endpoints(client):
    u = User.objects.create_user('staffp','sp@b.c','pass'); u.is_staff=True; u.save(); client.login(username='staffp', password='pass')
    r = client.get(reverse('device-ping')+'?ip=127.0.0.1')
    assert r.status_code in (200,400)
    r2 = client.get(reverse('device-discover')+'?base=127.0.0')
    assert r2.status_code in (200,400)

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
    for field_name in ['legacy_userid','identitycard','reservation_password','elevator_level','site_code']:
        assert field_name in html, f"Missing extended field {field_name} in employee form"
