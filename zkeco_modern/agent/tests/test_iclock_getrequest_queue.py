import pytest

from agent.models import AuditLog, CommandLog, Device, DevicePushSession


@pytest.mark.django_db
def test_iclock_getrequest_serves_adms_raw_commands_and_marks_sent(client):
    dev = Device.objects.create(
        name="CTRL_CMD",
        serial_number="SN_CMD_1",
        ip_address="192.168.50.10",
        port=4370,
        enabled=True,
    )

    c1 = CommandLog.objects.create(device=dev, command="ADMS_RAW:LINE1", status="PENDING")
    c2 = CommandLog.objects.create(device=dev, command="ADMS_RAW:LINE2\nLINE3", status="PENDING")

    r = client.get(f"/iclock/getrequest/?SN={dev.serial_number}", REMOTE_ADDR=str(dev.ip_address))
    assert r.status_code == 200
    body = (r.content or b"").decode("utf-8", "replace")
    assert body == "LINE1\nLINE2\nLINE3\n"

    c1.refresh_from_db()
    c2.refresh_from_db()
    assert c1.status == "SENT"
    assert c2.status == "SENT"
    assert c1.executed_at is not None
    assert c2.executed_at is not None

    # Best-effort durable audit record
    assert AuditLog.objects.filter(module="iclock", action__startswith="getrequest").exists()


@pytest.mark.django_db
def test_iclock_getrequest_returns_ok_when_no_commands(client):
    dev = Device.objects.create(
        name="CTRL_CMD2",
        serial_number="SN_CMD_2",
        ip_address="192.168.50.11",
        port=4370,
        enabled=True,
    )

    r = client.get(f"/iclock/getrequest/?SN={dev.serial_number}", REMOTE_ADDR=str(dev.ip_address))
    assert r.status_code == 200
    assert (r.content or b"").decode("utf-8", "replace") == "OK\n"

    session = DevicePushSession.objects.get(serial_number=dev.serial_number)
    assert session.last_poll_at is not None
