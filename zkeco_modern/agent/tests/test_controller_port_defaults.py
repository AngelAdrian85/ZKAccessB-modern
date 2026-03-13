import json
import socket

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from agent.models import Device
from agent.views import device_admin_test, device_port_test


class _Open14370Socket:
    def setblocking(self, flag):
        self._flag = flag

    def connect_ex(self, addr):
        _ip, port = addr
        return 0 if int(port) == 14370 else 10061

    def getsockopt(self, level, optname):
        return 0

    def close(self):
        return None


@pytest.mark.django_db
def test_device_port_test_defaults_to_route_aware_port_for_c3pro(monkeypatch):
    Device.objects.create(
        name="CTRL C3-100Pro",
        serial_number="SN-C3PRO-PORTTEST",
        ip_address="192.168.1.235",
        port=4370,
        hardware_version="ZMM200_C3Pro",
        firmware_version="AC Ver 4.7.8.3033 Aug 14 2023",
        enabled=True,
    )
    user = User.objects.create_user("staff_porttest", "pt@b.c", "pass")
    factory = RequestFactory()
    req = factory.get("/agent/devices/port-test/?ip=192.168.1.235")
    req.user = user

    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: _Open14370Socket())

    resp = device_port_test(req)
    body = json.loads(resp.content.decode("utf-8"))

    assert body["ok"] is True
    assert body["requested_ports"][0] == 14370
    assert body["best_port"] == 14370


@pytest.mark.django_db
def test_device_admin_test_defaults_to_route_aware_port_for_c3pro(monkeypatch):
    Device.objects.create(
        name="CTRL C3-100Pro",
        serial_number="SN-C3PRO-ADMINTEST",
        ip_address="192.168.1.235",
        port=4370,
        hardware_version="ZMM200_C3Pro",
        firmware_version="AC Ver 4.7.8.3033 Aug 14 2023",
        enabled=True,
    )
    user = User.objects.create_user("staff_admintest", "at@b.c", "pass")
    factory = RequestFactory()
    req = factory.get("/agent/devices/admin-test/?ip=192.168.1.235")
    req.user = user

    def fake_get_device_options(conn, items):
        if int(conn.ip_port) != 14370:
            return {"ok": False, "result": -2, "last_error": -2, "data": "", "dll_path_used": ""}
        return {
            "ok": True,
            "result": 0,
            "last_error": 0,
            "data": "IPAddress=192.168.1.235,DeviceName=CTRL C3-100Pro,Product=C3-100Pro,~SerialNumber=SN-C3PRO-ADMINTEST",
            "dll_path_used": "dll-x64",
        }

    monkeypatch.setattr("agent.views._get_default_comm_password_cached", lambda: "Zk@123")
    monkeypatch.setattr("agent.plcommpro_bridge.get_device_options", fake_get_device_options)

    resp = device_admin_test(req)
    body = json.loads(resp.content.decode("utf-8"))

    assert body["ok"] is True
    assert body["requested_port"] == 14370
    assert body["port"] == 14370
    assert body["attempts"][0]["port"] == 14370