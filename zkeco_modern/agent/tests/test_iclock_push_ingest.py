import pytest

from agent.models import Device, DeviceRealtimeLog


@pytest.mark.django_db
def test_iclock_cdata_accepts_unauth_and_persists_by_sn(client):
    dev = Device.objects.create(
        name="CTRL1",
        serial_number="SN_PUSH_1",
        ip_address="192.168.1.10",
        port=4370,
        enabled=True,
    )

    body = "2026-02-20 10:00:00,0,999999,1,0,0\n"
    r = client.post(
        f"/iclock/cdata/?SN={dev.serial_number}&table=rtlog",
        data=body,
        content_type="text/plain",
    )
    assert r.status_code == 200
    assert (r.content or b"").decode("utf-8", "ignore").strip().upper().startswith("OK")

    row = DeviceRealtimeLog.objects.order_by("-id").first()
    assert row is not None
    assert row.device_id == dev.id
    assert row.sn == dev.serial_number
    assert row.raw.strip() == "2026-02-20 10:00:00,0,999999,1,0,0"


@pytest.mark.django_db
def test_iclock_cdata_persists_by_remote_ip_when_sn_missing(client):
    dev = Device.objects.create(
        name="CTRL2",
        serial_number="SN_PUSH_2",
        ip_address="10.10.10.10",
        port=4370,
        enabled=True,
    )

    body = "2026-02-20 10:00:01,0,111111,2,0,0\n"
    r = client.post(
        "/iclock/cdata/?table=rtlog",
        data=body,
        content_type="text/plain",
        REMOTE_ADDR=str(dev.ip_address),
    )
    assert r.status_code == 200

    row = DeviceRealtimeLog.objects.order_by("-id").first()
    assert row is not None
    assert row.device_id == dev.id
    assert row.sn == dev.serial_number
    assert row.raw.strip() == "2026-02-20 10:00:01,0,111111,2,0,0"


@pytest.mark.django_db
def test_iclock_cdata_normalizes_tab_separated_lines(client):
    dev = Device.objects.create(
        name="CTRL3",
        serial_number="SN_PUSH_3",
        ip_address="192.168.1.11",
        port=4370,
        enabled=True,
    )

    body = "2026-02-20 10:00:02\t0\t222222\t3\t0\t0\n"
    r = client.post(
        f"/iclock/cdata/?SN={dev.serial_number}&table=rtlog",
        data=body,
        content_type="text/plain",
    )
    assert r.status_code == 200

    row = DeviceRealtimeLog.objects.order_by("-id").first()
    assert row is not None
    assert row.device_id == dev.id
    assert row.raw.strip() == "2026-02-20 10:00:02,0,222222,3,0,0"


@pytest.mark.django_db
def test_iclock_cdata_normalizes_headered_transaction_rows(client):
    dev = Device.objects.create(
        name="CTRL4",
        serial_number="SN_PUSH_4",
        ip_address="192.168.1.12",
        port=4370,
        enabled=True,
    )

    import datetime as dt

    base = dt.datetime(2000, 1, 1, 0, 0, 0)
    target = dt.datetime(2026, 2, 20, 10, 0, 3)
    secs = int((target - base).total_seconds())

    header = "Pin,Verified,DoorID,EventType,InOutState,Time_second,Index,Cardno,Sitecode"
    row = f"0,4,1,27,1,{secs},197,333333,0"
    body = header + "\n" + row + "\n"

    r = client.post(
        f"/iclock/cdata/?SN={dev.serial_number}&table=transaction",
        data=body,
        content_type="text/plain",
    )
    assert r.status_code == 200

    saved = DeviceRealtimeLog.objects.order_by("-id").first()
    assert saved is not None
    assert saved.device_id == dev.id
    assert saved.sn == dev.serial_number
    assert saved.raw.strip() == "2026-02-20 10:00:03,0,333333,1,27,4"


@pytest.mark.django_db
def test_iclock_cdata_normalizes_headerless_transaction_rows(client):
    dev = Device.objects.create(
        name="CTRL5",
        serial_number="SN_PUSH_5",
        ip_address="192.168.1.13",
        port=4370,
        enabled=True,
    )

    import datetime as dt

    base = dt.datetime(2000, 1, 1, 0, 0, 0)
    target = dt.datetime(2026, 2, 20, 10, 0, 4)
    secs = int((target - base).total_seconds())

    # Common transaction row without header.
    row = f"0,4,1,27,1,{secs},198,,0"
    body = row + "\n"

    r = client.post(
        f"/iclock/cdata/?SN={dev.serial_number}&table=transaction",
        data=body,
        content_type="text/plain",
    )
    assert r.status_code == 200

    saved = DeviceRealtimeLog.objects.order_by("-id").first()
    assert saved is not None
    assert saved.device_id == dev.id
    assert saved.sn == dev.serial_number
    # Cardno is empty -> third field empty.
    assert saved.raw.strip() == "2026-02-20 10:00:04,0,,1,27,4"
