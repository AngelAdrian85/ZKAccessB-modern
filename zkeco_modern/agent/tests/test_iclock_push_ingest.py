import pytest
import json
from unittest.mock import patch

from agent.models import Device, DevicePushSession, DeviceRealtimeLog
from agent import iclock_views


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


@pytest.mark.django_db
def test_iclock_broadcast_rtlog_batch_includes_controller_missing_card_status():
    captured = {}

    class _Layer:
        pass

    def _fake_async_to_sync(fn):
        def _wrapped(*args, **kwargs):
            return fn(*args, **kwargs)
        return _wrapped

    def _fake_group_send(group, message):
        captured["group"] = group
        captured["message"] = message

    layer = _Layer()
    layer.group_send = _fake_group_send

    with patch("channels.layers.get_channel_layer", return_value=layer), patch("asgiref.sync.async_to_sync", side_effect=_fake_async_to_sync):
        iclock_views._broadcast_rtlog_batch(22, ["2026-02-20 10:00:04,0,,1,27,4"])

    payload = captured["message"]["payload"]
    assert captured["group"] == "monitor"
    assert payload["type"] == "rtlog.batch"
    assert payload["device_id"] == 22
    assert payload["lines"] == ["2026-02-20 10:00:04,0,,1,27,4"]
    assert payload["entries"][0]["controller_event_status"] == "controller-event-without-cardno"
    assert payload["entries"][0]["controller_event_without_cardno"] is True
    assert payload["entries"][0]["card_display_status"] == "valid_without_cardno"
    assert payload["entries"][0]["card_display_label"] == "Valid fara CardNo"


@pytest.mark.django_db
def test_iclock_broadcast_rtlog_batch_enriches_missing_card_from_recent_external_reader():
    captured = {}

    class _Layer:
        pass

    def _fake_async_to_sync(fn):
        def _wrapped(*args, **kwargs):
            return fn(*args, **kwargs)
        return _wrapped

    def _fake_group_send(group, message):
        captured["group"] = group
        captured["message"] = message

    DeviceRealtimeLog.objects.create(
        device_id=22,
        sn="SN_PUSH_22",
        raw="2026-02-20 10:00:04,0,555444,1,0,CITITOR EXTERN,acp",
    )

    layer = _Layer()
    layer.group_send = _fake_group_send

    with patch("channels.layers.get_channel_layer", return_value=layer), patch("asgiref.sync.async_to_sync", side_effect=_fake_async_to_sync):
        iclock_views._broadcast_rtlog_batch(22, ["2026-02-20 10:00:05,0,,1,27,4"])

    payload = captured["message"]["payload"]
    entry = payload["entries"][0]
    assert captured["group"] == "monitor"
    assert entry["card_no"] == "555444"
    assert entry["enrichment_source"] == "external_reader_recent"
    assert entry["enrichment_status"] == "enriched"
    assert entry["controller_event_without_cardno"] is False
    assert entry["card_display_label"] == ""


@pytest.mark.django_db
def test_iclock_cdata_writes_capture_dump_for_missing_card_transaction(client, tmp_path, monkeypatch):
    dev = Device.objects.create(
        name="CTRL6",
        serial_number="SN_PUSH_6",
        ip_address="192.168.1.14",
        port=4370,
        enabled=True,
    )

    capture_file = tmp_path / "iclock_capture.jsonl"
    monkeypatch.setenv("ZKACCESS_ICLOCK_CAPTURE_FILE", str(capture_file))

    import datetime as dt

    base = dt.datetime(2000, 1, 1, 0, 0, 0)
    target = dt.datetime(2026, 2, 20, 10, 0, 5)
    secs = int((target - base).total_seconds())

    body = f"0,4,1,255,1,{secs},199,,0\n"
    r = client.post(
        f"/iclock/cdata/?SN={dev.serial_number}&table=transaction",
        data=body,
        content_type="text/plain",
    )
    assert r.status_code == 200
    assert capture_file.exists()

    rows = [json.loads(line) for line in capture_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    row = rows[0]
    assert row["device_id"] == dev.id
    assert row["sn"] == dev.serial_number
    assert row["table"] == "transaction"
    assert row["raw_lines"] == [body.strip()]
    assert row["normalized_lines"] == ["2026-02-20 10:00:05,0,,1,255,4"]
    assert row["suspicious"][0]["missing_card"] is True
    assert row["suspicious"][0]["event_255"] is True


@pytest.mark.django_db
def test_iclock_cdata_normalizes_key_value_transaction_card_alias(client):
    dev = Device.objects.create(
        name="CTRL7",
        serial_number="SN_PUSH_7",
        ip_address="192.168.1.15",
        port=4370,
        enabled=True,
    )

    import datetime as dt

    base = dt.datetime(2000, 1, 1, 0, 0, 0)
    target = dt.datetime(2026, 2, 20, 10, 0, 6)
    secs = int((target - base).total_seconds())

    body = f"pin=0\tverified=4\tdoorid=1\teventtype=27\tinoutstate=1\ttime_second={secs}\ttransaction cardno=444444\n"
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
    assert saved.raw.strip() == "2026-02-20 10:00:06,0,444444,1,27,4"


@pytest.mark.django_db
def test_iclock_cdata_writes_capture_dump_for_raw_suspicious_key_value_payload(client, tmp_path, monkeypatch):
    dev = Device.objects.create(
        name="CTRL8",
        serial_number="SN_PUSH_8",
        ip_address="192.168.1.16",
        port=4370,
        enabled=True,
    )

    capture_file = tmp_path / "iclock_capture_raw.jsonl"
    monkeypatch.setenv("ZKACCESS_ICLOCK_CAPTURE_FILE", str(capture_file))

    body = "pin=0\tverified=4\tdoorid=1\teventtype=255\n"
    r = client.post(
        f"/iclock/cdata/?SN={dev.serial_number}&table=transaction",
        data=body,
        content_type="text/plain",
    )
    assert r.status_code == 200
    assert capture_file.exists()

    rows = [json.loads(line) for line in capture_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    row = rows[0]
    assert row["device_id"] == dev.id
    assert row["normalized_lines"] == []
    assert row["raw_lines"] == [body.strip()]
    assert row["raw_line_details"][0]["event_code"] == "255"
    assert row["raw_line_details"][0]["missing_card"] is True


@pytest.mark.django_db
def test_iclock_cdata_normalizes_attlog_pin_card_timestamp_rows(client):
    dev = Device.objects.create(
        name="CTRL9",
        serial_number="SN_PUSH_9",
        ip_address="192.168.1.17",
        port=4370,
        enabled=True,
    )

    body = "ATTLOG\n1\t12345678\t2026-03-12 14:22:10\t0\t1\n"
    r = client.post(
        f"/iclock/cdata/?SN={dev.serial_number}&table=ATTLOG",
        data=body,
        content_type="text/plain",
    )
    assert r.status_code == 200

    saved = DeviceRealtimeLog.objects.order_by("-id").first()
    assert saved is not None
    assert saved.device_id == dev.id
    assert saved.sn == dev.serial_number
    assert saved.raw.strip() == "2026-03-12 14:22:10,1,12345678,1,0,0"


@pytest.mark.django_db
def test_iclock_getrawlog_alias_accepts_transaction_payload_and_captures_endpoint(client, tmp_path, monkeypatch):
    dev = Device.objects.create(
        name="CTRL10",
        serial_number="SN_PUSH_10",
        ip_address="192.168.1.18",
        port=4370,
        enabled=True,
    )

    capture_file = tmp_path / "iclock_capture_getrawlog.jsonl"
    monkeypatch.setenv("ZKACCESS_ICLOCK_CAPTURE_FILE", str(capture_file))
    monkeypatch.setenv("ZKACCESS_ICLOCK_CAPTURE_ALL", "1")

    body = "ATTLOG\n1\t987654\t2026-03-12 15:45:00\t0\t1\n"
    r = client.post(
        f"/iclock/getrawlog/?SN={dev.serial_number}&table=ATTLOG",
        data=body,
        content_type="text/plain",
    )
    assert r.status_code == 200

    saved = DeviceRealtimeLog.objects.order_by("-id").first()
    assert saved is not None
    assert saved.device_id == dev.id
    assert saved.raw.strip() == "2026-03-12 15:45:00,1,987654,1,0,0"

    rows = [json.loads(line) for line in capture_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    assert rows[0]["endpoint"] == "getrawlog"


@pytest.mark.django_db
def test_iclock_registry_accepts_controller_handshake_without_persisting_rtlog(client, tmp_path, monkeypatch):
    dev = Device.objects.create(
        name="CTRL11",
        serial_number="SN_PUSH_11",
        ip_address="192.168.1.19",
        port=4370,
        enabled=True,
    )

    capture_file = tmp_path / "iclock_capture_registry.jsonl"
    monkeypatch.setenv("ZKACCESS_ICLOCK_CAPTURE_FILE", str(capture_file))
    monkeypatch.setenv("ZKACCESS_ICLOCK_CAPTURE_ALL", "1")

    body = "DeviceType=acc,~DeviceName=C3-100Pro,FirmVer=AC Ver 4.7.8.3033 Aug 14 2023,authKey=\n"
    before = DeviceRealtimeLog.objects.count()

    r = client.post(
        f"/iclock/registry/?SN={dev.serial_number}",
        data=body,
        content_type="text/plain",
        REMOTE_ADDR=str(dev.ip_address),
    )
    assert r.status_code == 200
    response_body = (r.content or b"").decode("utf-8", "ignore")
    assert "registry=ok" in response_body
    assert "SessionID=" in response_body
    assert "PushProtVer=" in response_body
    assert DeviceRealtimeLog.objects.count() == before

    session = DevicePushSession.objects.get(serial_number=dev.serial_number)
    assert session.last_registry_at is not None
    assert session.session_id
    assert session.registry_code
    assert session.protocol_version_seen

    rows = [json.loads(line) for line in capture_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    row = rows[0]
    assert row["endpoint"] == "registry"
    assert row["device_id"] == dev.id
    assert row["resolved_sn"] == dev.serial_number
    assert row["normalized_lines"] == []
    assert row["raw_lines"] == [body.strip()]


@pytest.mark.django_db
def test_iclock_cdata_returns_explicit_push_options_when_requested(client, monkeypatch):
    dev = Device.objects.create(
        name="CTRL12",
        serial_number="SN_PUSH_12",
        ip_address="192.168.1.20",
        port=4370,
        enabled=True,
    )
    monkeypatch.setenv("ZKACCESS_PUSH_PROTOCOL_VERSION", "3.5")
    monkeypatch.setenv("ZKACCESS_PUSH_TIMEOUT_SEC", "180")

    r = client.post(
        f"/iclock/cdata/?SN={dev.serial_number}&options=all",
        data="",
        content_type="text/plain",
        REMOTE_ADDR=str(dev.ip_address),
    )
    assert r.status_code == 200
    body = (r.content or b"").decode("utf-8", "ignore")
    assert f"GET OPTION FROM:{dev.serial_number}" in body
    assert "ATTLOGStamp=None" in body
    assert "Delay=30" in body
    assert "TransTimes=00:00;24:00" in body
    assert "ServerVer=" in body
    assert "PushProtVer=3.5" in body
    assert "PushOptionsFlag=1" in body
    assert "PushOptions=" in body
    assert "TransTables=transaction,ATTLOG" in body
    assert "TimeoutSec=180" in body
    assert "SessionID=" in body


@pytest.mark.django_db
def test_iclock_registry_returns_extended_security_push_fields(client, monkeypatch):
    dev = Device.objects.create(
        name="CTRL12B",
        serial_number="SN_PUSH_12B",
        ip_address="192.168.1.120",
        port=4370,
        enabled=True,
    )
    monkeypatch.setenv("ZKACCESS_PUSH_SERVER_VERSION", "2.2.14")
    monkeypatch.setenv("ZKACCESS_PUSH_TRANS_TIMES", "06:00;23:00")
    monkeypatch.setenv("ZKACCESS_PUSH_DELAY", "45")

    r = client.post(
        f"/iclock/registry/?SN={dev.serial_number}",
        data="DeviceType=acc\n",
        content_type="text/plain",
        REMOTE_ADDR=str(dev.ip_address),
    )
    assert r.status_code == 200
    body = (r.content or b"").decode("utf-8", "ignore")
    assert "registry=ok" in body
    assert "ServerVer=2.2.14" in body
    assert "Delay=45" in body
    assert "TransTimes=06:00;23:00" in body
    assert "Realtime=1" in body


@pytest.mark.django_db
def test_iclock_auxiliary_endpoints_exist_and_touch_session(client):
    dev = Device.objects.create(
        name="CTRL13",
        serial_number="SN_PUSH_13",
        ip_address="192.168.1.21",
        port=4370,
        enabled=True,
    )

    r_control = client.post(
        f"/iclock/service/control/?SN={dev.serial_number}",
        data="cmd=sync",
        content_type="text/plain",
        REMOTE_ADDR=str(dev.ip_address),
    )
    assert r_control.status_code == 200

    r_query = client.get(
        f"/iclock/querydata/?SN={dev.serial_number}&options=all",
        REMOTE_ADDR=str(dev.ip_address),
    )
    assert r_query.status_code == 200
    assert "GET OPTION FROM:" in (r_query.content or b"").decode("utf-8", "ignore")

    r_file = client.post(
        f"/iclock/file/?SN={dev.serial_number}",
        data="file=request",
        content_type="text/plain",
        REMOTE_ADDR=str(dev.ip_address),
    )
    assert r_file.status_code == 200

    session = DevicePushSession.objects.get(serial_number=dev.serial_number)
    assert session.last_control_at is not None
    assert session.last_querydata_at is not None
    assert session.last_file_at is not None


@pytest.mark.django_db
def test_iclock_cdata_persists_session_correlation_payload(client):
    dev = Device.objects.create(
        name="CTRL14",
        serial_number="SN_PUSH_14",
        ip_address="192.168.1.22",
        port=4370,
        enabled=True,
    )

    r = client.post(
        f"/iclock/cdata/?SN={dev.serial_number}&table=transaction",
        data="2026-02-20 10:00:00,0,777777,1,0,0\n",
        content_type="text/plain",
        REMOTE_ADDR=str(dev.ip_address),
    )
    assert r.status_code == 200

    row = DeviceRealtimeLog.objects.order_by("-id").first()
    assert row is not None
    assert row.correlation_payload["endpoint"] == "cdata"
    assert row.correlation_payload["session_id"]


def test_extract_line_signal_values_maps_raw_transaction_positions():
    values = iclock_views._extract_line_signal_values("0,4,1,27,1,824896804,198,,0")
    assert values["card"] == ""
    assert values["event_code"] == "27"
    assert values["verify_mode"] == "4"
