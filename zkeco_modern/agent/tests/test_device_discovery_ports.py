from agent import device_discovery
from agent.device_discovery import DeviceIdentifier, ZKProtocol


class _FakeSocket:
    def __init__(self, attempts):
        self._attempts = attempts
        self._port = None

    def settimeout(self, timeout):
        self._timeout = timeout

    def connect(self, addr):
        _ip, port = addr
        self._attempts.append(int(port))
        self._port = int(port)
        if int(port) != 14370:
            raise ConnectionRefusedError()

    def send(self, payload):
        self._payload = payload

    def recv(self, size):
        return b"OK" if self._port == 14370 else b""

    def close(self):
        return None


def test_connect_and_identify_tries_common_ports_until_success(monkeypatch):
    attempts = []

    def _socket_factory(*args, **kwargs):
        return _FakeSocket(attempts)

    monkeypatch.setattr(device_discovery.socket, "socket", _socket_factory)

    result = ZKProtocol.connect_and_identify("192.168.1.10", port=4370, timeout=0.1)

    assert attempts[:2] == [4370, 14370]
    assert result is not None
    assert result["port"] == 14370
    assert result["connectivity"] == "tcp"


def test_create_device_from_discovery_preserves_detected_port():
    payload = DeviceIdentifier.create_device_from_discovery(
        {
            "ip": "192.168.1.10",
            "port": 14370,
            "serial_number": "SN14370",
            "device_type": "access_panel",
            "firmware_version": "fw",
            "connectivity": "tcp",
        }
    )

    assert payload["port"] == 14370
    assert payload["ip_address"] == "192.168.1.10"
