import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_employee_list_shows_employees(client):
    try:
        from legacy_models.models import Employee
    except Exception:
        pytest.skip("legacy_models not available")

    # Ensure a clean slate for the test DB
    Employee.objects.all().delete()
    Employee.objects.create(userid=1001, firstname="Test", lastname="User")

    from django.test import RequestFactory
    from iaccess_port import views as iaccess_views

    rf = RequestFactory()
    req = rf.get('/iaccess/employees/')
    resp = iaccess_views.employee_list(req)
    assert resp.status_code == 200
    body = resp.content.decode('utf-8')
    assert "Test User" in body


@pytest.mark.django_db
def test_device_list_shows_devices(client):
    try:
        from legacy_models.models import Device
    except Exception:
        pytest.skip("legacy_models not available")

    Device.objects.all().delete()
    Device.objects.create(device_name="ACPanel-99", sn="SN12345")

    from django.test import RequestFactory
    from iaccess_port import views as iaccess_views

    rf = RequestFactory()
    req = rf.get('/iaccess/devices/')
    resp = iaccess_views.device_list(req)
    assert resp.status_code == 200
    body = resp.content.decode('utf-8')
    assert "ACPanel-99" in body


@pytest.mark.django_db
def test_door_list_shows_doors(client):
    try:
        from legacy_models.models import Door
    except Exception:
        pytest.skip("legacy_models not available")

    Door.objects.all().delete()
    Door.objects.create(name="Main Entrance")

    from django.test import RequestFactory
    from iaccess_port import views as iaccess_views

    rf = RequestFactory()
    req = rf.get('/iaccess/doors/')
    resp = iaccess_views.door_list(req)
    assert resp.status_code == 200
    body = resp.content.decode('utf-8')
    assert "Main Entrance" in body
