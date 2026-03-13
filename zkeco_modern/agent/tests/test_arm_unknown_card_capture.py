import pytest

from agent.management.commands.arm_unknown_card_capture import build_capture_config, capture_status, detect_local_server_url
from agent.models import Device, Door


@pytest.mark.django_db
def test_build_capture_config_defaults_to_zkemkeeper_and_resolves_first_door():
    device = Device.objects.create(
        name="CTRL_CAPTURE",
        serial_number="SN_CAPTURE_1",
        ip_address="192.168.1.235",
        port=14370,
        comm_password="Zk@123",
        enabled=True,
    )
    door = Door.objects.create(device=device, name="Main Door", door_number=1)

    config = build_capture_config(
        device=device,
        strategy="auto",
        server_url="http://127.0.0.1:15437",
    )

    assert detect_local_server_url("http://127.0.0.1:9000/") == "http://127.0.0.1:9000"
    assert config["strategy"] == "zkemkeeper"
    assert config["device_id"] == device.id
    assert config["ip"] == "192.168.1.235"
    assert config["port"] == 14370
    assert config["door_pk"] == door.id
    assert config["door_number"] == "1"
    assert config["server_url"] == "http://127.0.0.1:15437"
    assert config["command"][0].lower() == "cscript.exe"
    assert any("/DoorPk:" in part for part in config["command"])
    assert config["sdk_dir"]
    assert any(str(part).startswith("/SdkDir:") for part in config["command"])


@pytest.mark.django_db
def test_build_capture_config_w26_uses_listener_command():
    device = Device.objects.create(
        name="CTRL_CAPTURE_W26",
        serial_number="SN_CAPTURE_W26",
        ip_address="192.168.1.236",
        port=14370,
        enabled=True,
    )

    config = build_capture_config(
        device=device,
        strategy="w26",
        server_url="http://127.0.0.1:15437",
        listen_port=9105,
        format_name="Wiegand 26",
    )

    assert config["strategy"] == "w26"
    assert config["listen_port"] == 9105
    assert config["format_name"] == "Wiegand 26"
    assert str(config["command"][1]).endswith("scripts\\wiegand_listener.py") or str(config["command"][1]).endswith("scripts/wiegand_listener.py")
    assert "--listen-port" in config["command"]


def test_capture_status_handles_missing_dump_file_cleanly():
    report = capture_status(
        {
            "strategy": "w26",
            "heartbeat_path": "",
            "dump_file": "",
        }
    )

    assert report["dump_exists"] is False
    assert report["dump_size"] == 0