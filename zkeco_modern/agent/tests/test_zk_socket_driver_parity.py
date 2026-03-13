import struct

import pytest

from agent import controller_provisioning
from agent import plcommpro_bridge
from agent.controller_provisioning import bind_controller, parse_search_device_output, parse_option_pairs, snapshot_controller
from agent.drivers.plcommpro_bridge_driver import PlcommproBridgeDriver
from agent.drivers.zk_socket_driver import ZKTechSocketDriver
from agent.models import Device, DeviceStatus


class _BridgeStub:
    def __init__(self):
        self.calls = []

    def get_options(self, items: str):
        self.calls.append(("get_options", items))
        return {"result": 0, "data": "IPAddress=192.168.1.10,DeviceName=C3-100,~SerialNumber=SN100"}

    def query_data(self, table: str, fields: str = "*", filter: str = "", option: str = ""):
        self.calls.append(("query_data", table, fields, filter, option))
        return {"result": 0, "data": "Pin,CardNo\r\n1,100"}

    def update_data(self, table: str, data: str, option: str = ""):
        self.calls.append(("update_data", table, data, option))
        return {"result": 0, "data": "ok"}

    def delete_data(self, table: str, filter: str = ""):
        self.calls.append(("delete_data", table, filter))
        return {"result": 0, "data": "ok"}

    def Get_Data_Count(self, table: str):
        self.calls.append(("Get_Data_Count", table))
        return {"result": 3}


def _clear_bridge_env(monkeypatch):
    monkeypatch.delenv("ZKACCESS_PLCOMMPRO_DLL", raising=False)
    monkeypatch.delenv("ZKACCESS_BRIDGE_EXE", raising=False)


@pytest.mark.django_db
def test_zk_socket_driver_uses_bridge_for_table_parity(monkeypatch):
    dev = Device.objects.create(name="CTRL_SOCKET", serial_number="SN_SOCKET_1", ip_address="192.168.1.10", port=4370, enabled=True)
    drv = ZKTechSocketDriver(dev)
    stub = _BridgeStub()
    monkeypatch.setattr(drv, "_bridge", lambda: stub)

    assert drv.get_options("IPAddress")["transport"] == "bridge-fallback"
    assert drv.query_data("user", "Pin,CardNo", filter="Pin=1", option="")["transport"] == "bridge-fallback"
    assert drv.update_data("user", "Pin=1", "")["transport"] == "bridge-fallback"
    assert drv.delete_data("user", "Pin=1")["transport"] == "bridge-fallback"
    assert drv.Get_Data_Count("user")["transport"] == "bridge-fallback"

    assert ("get_options", "IPAddress") in stub.calls
    assert any(call[0] == "query_data" and call[1] == "user" for call in stub.calls)


def test_parse_controller_search_and_options_helpers():
    devices = parse_search_device_output("IPAddress=192.168.1.10,SN=SN100,DeviceName=C3,Product=C3-100Pro")
    assert devices and devices[0]["ip"] == "192.168.1.10"
    assert devices[0]["serial_number"] == "SN100"
    opts = parse_option_pairs("IPAddress=192.168.1.10,DeviceName=C3-100,~SerialNumber=SN100")
    assert opts["IPAddress"] == "192.168.1.10"
    assert opts["DeviceName"] == "C3-100"


@pytest.mark.django_db
def test_zk_socket_driver_get_options_prefers_socket_when_connected(monkeypatch):
    dev = Device.objects.create(name="CTRL_SOCKET_NATIVE", serial_number="SN_SOCKET_NATIVE", ip_address="192.168.1.10", port=4370, enabled=True)
    drv = ZKTechSocketDriver(dev)

    class _Sock:
        def send(self, payload):
            self.payload = payload

    payload = b"IPAddress=192.168.1.10,DeviceName=C3-100"
    response = struct.pack("<hhhhh", drv.CMD_GETOPTIONS, 1, 1, 1, len(payload)) + payload + struct.pack("<h", 0)
    monkeypatch.setattr(drv, "socket", _Sock())
    monkeypatch.setattr(drv, "_recv_all", lambda max_size=4096: response)
    monkeypatch.setattr(drv, "_is_connected", lambda: True)

    resp = drv.get_options("IPAddress,DeviceName")

    assert resp["transport"] == "socket-native"
    assert resp["ok"] is True
    assert "DeviceName=C3-100" in resp["data"]


@pytest.mark.django_db
def test_zk_socket_driver_query_data_transaction_prefers_socket(monkeypatch):
    dev = Device.objects.create(name="CTRL_SOCKET_TXN", serial_number="SN_SOCKET_TXN", ip_address="192.168.1.10", port=4370, enabled=True)
    drv = ZKTechSocketDriver(dev)
    monkeypatch.setattr(drv, "_is_connected", lambda: True)
    monkeypatch.setattr(drv, "get_transaction", lambda newlog=False: {"result": 2, "data": {1: "1,2,3", 2: "4,5,6"}})

    resp = drv.query_data("transaction", fields="*", option="NewRecord")

    assert resp["transport"] == "socket-native"
    assert resp["result"] == 2
    assert resp["data"] == "1,2,3\r\n4,5,6"


@pytest.mark.django_db
def test_zk_socket_driver_data_count_transaction_prefers_socket(monkeypatch):
    dev = Device.objects.create(name="CTRL_SOCKET_CNT", serial_number="SN_SOCKET_CNT", ip_address="192.168.1.10", port=4370, enabled=True)
    drv = ZKTechSocketDriver(dev)
    monkeypatch.setattr(drv, "_is_connected", lambda: True)
    monkeypatch.setattr(drv, "get_transaction", lambda newlog=False: {"result": 7, "data": {}})

    resp = drv.Get_Data_Count("transaction")

    assert resp["transport"] == "socket-native"
    assert resp["result"] == 7


def test_snapshot_controller_falls_back_to_socket_options(monkeypatch):
    monkeypatch.setattr(controller_provisioning, "get_device_options", lambda conn, items: {"result": -2, "ok": False, "data": ""})
    monkeypatch.setattr(controller_provisioning, "_native_socket_get_options", lambda target, items: {"result": 1, "ok": True, "data": "IPAddress=192.168.1.55,DeviceName=C3-100,~SerialNumber=SN55", "transport": "socket-native"})
    monkeypatch.setattr(controller_provisioning, "data_count", lambda conn, table: {"result": 0})
    monkeypatch.setattr(controller_provisioning, "query_data", lambda conn, table, fields="*", option="": {"result": 0, "data": "header"})

    snapshot = snapshot_controller(controller_provisioning.ProvisionTarget(ip="192.168.1.55", port=4370, password="0"), table_names=("user",))

    assert snapshot["options_ok"] is True
    assert snapshot["option_transport"] == "socket-native"
    assert snapshot["identify"]["serial_number"] == "SN55"


def test_snapshot_controller_retries_option_items_individually(monkeypatch):
    def fake_get_options(conn, items):
        if "," in items:
            return {"result": -2, "ok": False, "data": ""}
        mapping = {
            "IPAddress": "IPAddress=192.168.1.77",
            "~SerialNumber": "~SerialNumber=SN77",
            "DeviceName": "DeviceName=C3-100",
        }
        return {"result": 0, "ok": True, "data": mapping.get(items, "")}

    monkeypatch.setattr(controller_provisioning, "get_device_options", fake_get_options)
    monkeypatch.setattr(controller_provisioning, "data_count", lambda conn, table: {"result": 0})
    monkeypatch.setattr(controller_provisioning, "query_data", lambda conn, table, fields="*", option="": {"result": 0, "data": "header"})

    snapshot = snapshot_controller(
        controller_provisioning.ProvisionTarget(ip="192.168.1.77", port=4370, password="0"),
        option_items="IPAddress,~SerialNumber,DeviceName",
        table_names=("user",),
    )

    assert snapshot["options_ok"] is True
    assert snapshot["options"]["IPAddress"] == "192.168.1.77"
    assert snapshot["identify"]["serial_number"] == "SN77"


def test_snapshot_controller_retries_14370_when_requested_port_fails(monkeypatch):
    def fake_get_options(conn, items):
        if int(conn.ip_port) == 4370:
            return {"result": -2, "ok": False, "data": "connect failed"}
        if int(conn.ip_port) == 14370:
            return {
                "result": 0,
                "ok": True,
                "data": "IPAddress=192.168.1.235,DeviceName=CTRL C3-100Pro,Product=C3-100Pro,TCPPort=14370,~SerialNumber=SN235",
            }
        return {"result": -2, "ok": False, "data": "unexpected port"}

    monkeypatch.setattr(controller_provisioning, "get_device_options", fake_get_options)
    monkeypatch.setattr(controller_provisioning, "data_count", lambda conn, table: {"result": 0})
    monkeypatch.setattr(controller_provisioning, "query_data", lambda conn, table, fields="*", option="": {"result": 0, "data": "header"})

    snapshot = snapshot_controller(controller_provisioning.ProvisionTarget(ip="192.168.1.235", port=4370, password="0"), table_names=("user",))

    assert snapshot["options_ok"] is True
    assert snapshot["option_requested_port"] == 4370
    assert snapshot["option_resolved_port"] == 14370
    assert snapshot["target"]["configured_port"] == 4370
    assert snapshot["target"]["port"] == 14370
    assert snapshot["route_resolution"]["effective_port"] == 14370
    assert snapshot["identify"]["serial_number"] == "SN235"


def test_get_device_options_learns_per_item_dll_affinity(monkeypatch):
    _clear_bridge_env(monkeypatch)
    conn = plcommpro_bridge.PlcommproConnInfo(ipaddress="192.168.1.235", ip_port=14370, password="", timeout=3000)
    plcommpro_bridge._DLL_HINTS.clear()
    plcommpro_bridge._OPTION_DLL_HINTS.clear()

    monkeypatch.setattr(plcommpro_bridge, "_preferred_plcommpro_arch", lambda: "x86")
    monkeypatch.setattr(plcommpro_bridge, "_plcommpro_repo_candidates", lambda arch="x86": ["dll-a", "dll-ip", "dll-serial"])
    monkeypatch.setattr(plcommpro_bridge, "_plcommpro_extra_dirs_candidates", lambda: [])
    monkeypatch.setattr(plcommpro_bridge, "_is_viable_x86_dll", lambda path: path in {"dll-a", "dll-ip", "dll-serial"})

    def fake_run_bridge_single(request, py_bridge=None):
        item = str(request.get("items") or "")
        dll = str(request.get("dll_path") or "")
        if item == "IPAddress,~SerialNumber":
            return {"ok": False, "result": -2, "data": "connect failed"}
        if item == "IPAddress" and dll == "dll-ip":
            return {"ok": True, "result": 0, "data": "IPAddress=192.168.1.235"}
        if item == "~SerialNumber" and dll == "dll-serial":
            return {"ok": True, "result": 0, "data": "~SerialNumber=SN235"}
        return {"ok": False, "result": -2, "data": "connect failed"}

    monkeypatch.setattr(plcommpro_bridge, "_run_bridge_single", fake_run_bridge_single)

    resp = plcommpro_bridge.get_device_options(conn, "IPAddress,~SerialNumber")

    assert resp["ok"] is True
    assert "IPAddress=192.168.1.235" in resp["data"]
    assert "~SerialNumber=SN235" in resp["data"]
    assert plcommpro_bridge._OPTION_DLL_HINTS[("192.168.1.235", 14370, "ipaddress")] == "dll-ip"
    assert plcommpro_bridge._OPTION_DLL_HINTS[("192.168.1.235", 14370, "~serialnumber")] == "dll-serial"


def test_get_device_options_uses_cached_item_affinity_first(monkeypatch):
    _clear_bridge_env(monkeypatch)
    conn = plcommpro_bridge.PlcommproConnInfo(ipaddress="192.168.1.235", ip_port=14370, password="", timeout=3000)
    plcommpro_bridge._DLL_HINTS.clear()
    plcommpro_bridge._OPTION_DLL_HINTS.clear()
    plcommpro_bridge._OPTION_DLL_HINTS[("192.168.1.235", 14370, "~serialnumber")] = "dll-serial"

    monkeypatch.setattr(plcommpro_bridge, "_preferred_plcommpro_arch", lambda: "x86")
    monkeypatch.setattr(plcommpro_bridge, "_plcommpro_repo_candidates", lambda arch="x86": ["dll-a", "dll-serial", "dll-ip"])
    monkeypatch.setattr(plcommpro_bridge, "_plcommpro_extra_dirs_candidates", lambda: [])
    monkeypatch.setattr(plcommpro_bridge, "_is_viable_x86_dll", lambda path: path in {"dll-a", "dll-ip", "dll-serial"})

    calls = []

    def fake_run_bridge_single(request, py_bridge=None):
        item = str(request.get("items") or "")
        dll = str(request.get("dll_path") or "")
        calls.append((item, dll))
        if item == "~SerialNumber" and dll == "dll-serial":
            return {"ok": True, "result": 0, "data": "~SerialNumber=SN235"}
        return {"ok": False, "result": -2, "data": "connect failed"}

    monkeypatch.setattr(plcommpro_bridge, "_run_bridge_single", fake_run_bridge_single)

    resp = plcommpro_bridge.get_device_options(conn, "~SerialNumber")

    assert resp["ok"] is True
    assert calls[0] == ("~SerialNumber", "dll-serial")


def test_get_device_options_fallback_preserves_meta_alias_and_note(monkeypatch):
    _clear_bridge_env(monkeypatch)
    conn = plcommpro_bridge.PlcommproConnInfo(ipaddress="192.168.1.235", ip_port=14370, password="", timeout=3000)
    plcommpro_bridge._DLL_HINTS.clear()
    plcommpro_bridge._OPTION_DLL_HINTS.clear()

    monkeypatch.setattr(plcommpro_bridge, "_preferred_plcommpro_arch", lambda: "x86")
    monkeypatch.setattr(plcommpro_bridge, "_plcommpro_repo_candidates", lambda arch="x86": ["dll-a", "dll-ip", "dll-serial"])
    monkeypatch.setattr(plcommpro_bridge, "_plcommpro_extra_dirs_candidates", lambda: [])
    monkeypatch.setattr(plcommpro_bridge, "_is_viable_x86_dll", lambda path: path in {"dll-a", "dll-ip", "dll-serial"})

    def fake_run_bridge_single(request, py_bridge=None):
        item = str(request.get("items") or "")
        dll = str(request.get("dll_path") or "")
        if item == "IPAddress,~SerialNumber":
            return {
                "ok": False,
                "result": -2,
                "data": "connect failed",
                "action_alias": "identify_controller",
                "note": "bulk read failed",
                "meta": {"line_count": 0},
            }
        if item == "IPAddress" and dll == "dll-ip":
            return {
                "ok": True,
                "result": 0,
                "data": "IPAddress=192.168.1.235",
                "action_alias": "option_read",
                "note": "IPAddress via dll-ip",
                "meta": {"line_count": 1, "first_line": "IPAddress=192.168.1.235"},
            }
        if item == "~SerialNumber" and dll == "dll-serial":
            return {
                "ok": True,
                "result": 0,
                "data": "~SerialNumber=SN235",
                "action_alias": "identify_controller",
                "note": "serial via dll-serial",
                "meta": {"line_count": 1, "first_line": "~SerialNumber=SN235"},
            }
        return {"ok": False, "result": -2, "data": "connect failed", "meta": {}}

    monkeypatch.setattr(plcommpro_bridge, "_run_bridge_single", fake_run_bridge_single)

    resp = plcommpro_bridge.get_device_options(conn, "IPAddress,~SerialNumber")

    assert resp["ok"] is True
    assert resp["action_alias"] == "identify_controller"
    assert "bulk read failed" in resp["note"]
    assert resp["meta"]["fallback_mode"] == "item-by-item"
    assert resp["meta"]["resolved_items"] == ["IPAddress", "~SerialNumber"]
    assert resp["meta"]["item_action_aliases"]["IPAddress"] == "option_read"


def test_bridge_driver_get_options_exposes_bridge_observability(monkeypatch):
    dev = Device(name="CTRL_BRIDGE_META", serial_number="SN_BRIDGE_META", ip_address="192.168.1.50", port=4370, enabled=True)
    drv = PlcommproBridgeDriver(dev)

    monkeypatch.setattr(
        "agent.drivers.plcommpro_bridge_driver.get_device_options",
        lambda conn, items, process_timeout_s=None: {
            "ok": True,
            "result": 0,
            "data": "IPAddress=192.168.1.50",
            "transport": "bridge",
            "action_alias": "option_read",
            "note": "single item read",
            "meta": {"line_count": 1},
            "dll_path_used": "dll-meta",
        },
    )

    resp = drv.get_options("IPAddress")

    assert resp["result"] == 0
    assert resp["action_alias"] == "option_read"
    assert resp["note"] == "single item read"
    assert resp["meta"]["line_count"] == 1
    assert resp["dll_path_used"] == "dll-meta"


def test_query_data_user_learns_query_affinity(monkeypatch):
    _clear_bridge_env(monkeypatch)
    conn = plcommpro_bridge.PlcommproConnInfo(ipaddress="192.168.1.235", ip_port=14370, password="", timeout=3000)
    plcommpro_bridge._DLL_HINTS.clear()
    plcommpro_bridge._QUERY_DLL_HINTS.clear()

    monkeypatch.setattr(plcommpro_bridge, "_preferred_plcommpro_arch", lambda: "x86")
    monkeypatch.setattr(plcommpro_bridge, "_plcommpro_repo_candidates", lambda arch="x86": ["dll-a", "dll-user"])
    monkeypatch.setattr(plcommpro_bridge, "_plcommpro_extra_dirs_candidates", lambda: [])
    monkeypatch.setattr(plcommpro_bridge, "_is_viable_x86_dll", lambda path: path in {"dll-a", "dll-user"})

    def fake_run_bridge_single(request, py_bridge=None):
        table = str(request.get("table") or "")
        dll = str(request.get("dll_path") or "")
        fields = str(request.get("fields") or "")
        if table == "user" and fields == "Pin,CardNo,ViceCard,Group" and dll == "dll-user":
            return {"ok": True, "result": 1, "data": "Pin,CardNo,ViceCard,Group\r\n1,100,200,7"}
        return {"ok": False, "result": -2, "data": "connect failed"}

    monkeypatch.setattr(plcommpro_bridge, "_run_bridge_single", fake_run_bridge_single)

    resp = plcommpro_bridge.query_data(conn, table="user", fields="Pin,CardNo,ViceCard,Group", filter="Pin=1", option="")

    assert resp["ok"] is True
    assert plcommpro_bridge._QUERY_DLL_HINTS[("192.168.1.235", 14370, "user", "pin,cardno,vicecard,group")] == "dll-user"


def test_query_data_user_uses_cached_affinity_first(monkeypatch):
    _clear_bridge_env(monkeypatch)
    conn = plcommpro_bridge.PlcommproConnInfo(ipaddress="192.168.1.235", ip_port=14370, password="", timeout=3000)
    plcommpro_bridge._DLL_HINTS.clear()
    plcommpro_bridge._QUERY_DLL_HINTS.clear()
    plcommpro_bridge._QUERY_DLL_HINTS[("192.168.1.235", 14370, "user", "pin,cardno")] = "dll-user"

    monkeypatch.setattr(plcommpro_bridge, "_preferred_plcommpro_arch", lambda: "x86")
    monkeypatch.setattr(plcommpro_bridge, "_plcommpro_repo_candidates", lambda arch="x86": ["dll-a", "dll-user"])
    monkeypatch.setattr(plcommpro_bridge, "_plcommpro_extra_dirs_candidates", lambda: [])
    monkeypatch.setattr(plcommpro_bridge, "_is_viable_x86_dll", lambda path: path in {"dll-a", "dll-user"})

    calls = []

    def fake_run_bridge_single(request, py_bridge=None):
        table = str(request.get("table") or "")
        dll = str(request.get("dll_path") or "")
        fields = str(request.get("fields") or "")
        calls.append((table, fields, dll))
        if table == "user" and fields == "Pin,CardNo" and dll == "dll-user":
            return {"ok": True, "result": 1, "data": "Pin,CardNo\r\n1,100"}
        return {"ok": False, "result": -2, "data": "connect failed"}

    monkeypatch.setattr(plcommpro_bridge, "_run_bridge_single", fake_run_bridge_single)

    resp = plcommpro_bridge.query_data(conn, table="user", fields="Pin,CardNo", filter="Pin=1", option="")

    assert resp["ok"] is True
    assert calls[0] == ("user", "Pin,CardNo", "dll-user")


@pytest.mark.django_db
def test_bind_controller_creates_device_status_and_doors():
    snapshot = {
        "target": {"ip": "192.168.1.55", "port": 4370},
        "identify": {"ip": "192.168.1.55", "serial_number": "SN_BIND_1", "device_name": "C3-200", "product": "C3-200"},
        "options": {"IPAddress": "192.168.1.55", "NetMask": "255.255.255.0", "GATEIPAddress": "192.168.1.254", "Product": "C3-200"},
        "options_ok": True,
    }

    result = bind_controller(snapshot, comm_password="0")
    dev = Device.objects.get(pk=result["device_id"])
    status = DeviceStatus.objects.get(device=dev)

    assert dev.ip_address == "192.168.1.55"
    assert dev.serial_number == "SN_BIND_1"
    assert status.online is True
    assert result["door_capacity"] == 2


@pytest.mark.django_db
def test_bind_controller_persists_firmware_tcp_port_and_version():
    snapshot = {
        "target": {"ip": "192.168.1.235", "port": 4370, "configured_port": 4370},
        "identify": {"ip": "192.168.1.235", "serial_number": "SN_BIND_14370", "device_name": "C3-100Pro", "product": "ZMM200_C3Pro"},
        "options": {
            "IPAddress": "192.168.1.235",
            "DeviceName": "C3-100Pro",
            "Platform": "ZMM200_C3Pro",
            "TCPPort": "14370",
            "FirmVer": "AC Ver 4.7.8.3033 Aug 14 2023",
        },
        "options_ok": True,
    }

    result = bind_controller(snapshot, comm_password="0")
    dev = Device.objects.get(pk=result["device_id"])

    assert dev.port == 14370
    assert dev.firmware_version == "AC Ver 4.7.8.3033 Aug 14 2023"
    assert result["effective_port"] == 14370


def test_plcommpro_bridge_driver_prefers_firmware_route_port_candidates():
    dev = Device(
        name="CTRL C3-100Pro",
        serial_number="SN_ROUTE_1",
        ip_address="192.168.1.235",
        port=4370,
        hardware_version="ZMM200_C3Pro",
        firmware_version="AC Ver 4.7.8.3033 Aug 14 2023",
        enabled=True,
    )

    drv = PlcommproBridgeDriver(dev)

    assert drv._port_candidates()[:2] == [14370, 4370]