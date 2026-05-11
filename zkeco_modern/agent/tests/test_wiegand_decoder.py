import json
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import RequestFactory

from agent.models import Device, DeviceEventLog, DeviceRealtimeLog, Door, WiegandCardFormat
from agent.uid_correlation import resolve_controller_uid
from agent.views import card_read_push, card_read_wait
from agent.wiegand_decoder import decode_wiegand, list_known_wiegand_formats


def test_decode_wiegand_34_extracts_card_number_and_parity():
    decoded = decode_wiegand(
        bits="0000000000111010011001011101100010",
        format_name="Wiegand 34",
    )

    assert decoded["card_number"] == "7654321"
    assert decoded["parity_ok"] is True
    assert decoded["format_name"] == "Wiegand 34"


def test_decode_wiegand_35_extracts_site_and_card_number():
    decoded = decode_wiegand(
        bits="00000101000001000111100010010000000",
        format_name="Wiegand 35",
    )

    assert decoded["card_number"] == "123456"
    assert decoded["site_code"] == 321
    assert decoded["parity_ok"] is True


def test_list_known_wiegand_formats_includes_defaults():
    names = {row["name"] for row in list_known_wiegand_formats()}

    assert "Wiegand 34" in names
    assert "Wiegand 35" in names
    assert "Wiegand 26" in names


def test_card_read_push_decodes_wiegand_and_wait_returns_it():
    cache.delete("agent:last_card_read")
    factory = RequestFactory()
    payload = {
        "source": "unknown-card",
        "wiegand_bits": "00000101000001000111100010010000000",
        "wiegand_format": "Wiegand 35",
    }
    req = factory.post(
        "/agent/api/cards/read/push/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    resp = card_read_push(req)
    body = json.loads(resp.content.decode("utf-8"))

    assert body["ok"] is True
    assert body["wiegand"]["card_number"] == "123456"
    assert body["wiegand"]["site_code"] == 321

    wait_req = factory.get("/agent/api/cards/read/wait/")
    wait_resp = card_read_wait(wait_req)
    wait_body = json.loads(wait_resp.content.decode("utf-8"))

    assert wait_body["ok"] is True
    assert wait_body["card_number"] == "123456"
    assert wait_body["wiegand"]["format_name"] == "Wiegand 35"


@pytest.mark.django_db
def test_card_read_push_prefers_active_wiegand_format_for_ambiguous_w26_length():
    cache.delete("agent:last_card_read")
    WiegandCardFormat.objects.all().update(is_active=False)
    WiegandCardFormat.objects.create(
        wiegand_name="Test Wiegand 26a Active",
        is_active=True,
        wiegand_count=26,
        wiegand_mode=1,
        even_parity_start=1,
        even_parity_count=13,
        odd_parity_start=14,
        odd_parity_count=13,
        cid_start=10,
        cid_count=16,
        facility_code_start=2,
        facility_code_count=8,
    )

    factory = RequestFactory()
    payload = {
        "source": "reader-w26",
        "wiegand_bits": "10000011100110000001110010",
    }
    req = factory.post(
        "/agent/api/cards/read/push/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    resp = card_read_push(req)
    body = json.loads(resp.content.decode("utf-8"))

    assert body["ok"] is True
    assert body["card_number"] == "12345"
    assert body["wiegand"]["format_name"] == "Test Wiegand 26a Active"
    assert body["wiegand"]["facility_code"] == 7


@pytest.mark.django_db
def test_card_read_push_accepts_zkemkeeper_onhidnum_payload_without_card_number():
    cache.delete("agent:last_card_read")
    factory = RequestFactory()
    payload = {
        "source": "zkemkeeper-c22",
        "zkemkeeper_event": "OnHIDNum",
        "zkemkeeper_hid_card": "00-00-12-34",
        "zkemkeeper_properties": {
            "CardNumber": "00001234",
            "HIDNum": "4660",
        },
        "zkemkeeper_source_args": ["00001234"],
    }
    req = factory.post(
        "/agent/api/cards/read/push/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    before_rtlog = DeviceRealtimeLog.objects.count()
    before_evt = DeviceEventLog.objects.count()

    resp = card_read_push(req)
    body = json.loads(resp.content.decode("utf-8"))

    assert body["ok"] is True
    assert body["card_number"] == "1234"
    assert DeviceRealtimeLog.objects.count() == before_rtlog + 1
    assert DeviceEventLog.objects.count() == before_evt + 1

    last_rtlog = DeviceRealtimeLog.objects.order_by("-id").first()
    assert last_rtlog is not None
    assert ",1234," in str(last_rtlog.raw or "")

    last_event = DeviceEventLog.objects.order_by("-id").first()
    assert last_event is not None
    payload_saved = json.loads(str(last_event.raw_line or "{}"))
    assert payload_saved["card_number"] == "1234"
    assert payload_saved["zkemkeeper_event"] == "OnHIDNum"
    assert payload_saved["zkemkeeper_card_meta"]["selected"]["normalized"] == "1234"


@pytest.mark.django_db
def test_card_read_push_monitor_payload_includes_rtlog_row_id_and_source():
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

    factory = RequestFactory()
    req = factory.post(
        "/agent/api/cards/read/push/",
        data=json.dumps({"card_number": "555444", "source": "acp"}),
        content_type="application/json",
    )

    with patch("channels.layers.get_channel_layer", return_value=layer), patch("asgiref.sync.async_to_sync", side_effect=_fake_async_to_sync):
        resp = card_read_push(req)

    body = json.loads(resp.content.decode("utf-8"))
    assert body["ok"] is True
    assert captured["group"] == "monitor"

    payload = captured["message"]["payload"]
    assert payload["type"] == "rtlog.batch"
    assert payload["lines"]
    assert payload["entries"]

    entry = payload["entries"][0]
    last_rtlog = DeviceRealtimeLog.objects.order_by("-id").first()
    assert last_rtlog is not None
    assert entry["id"] == last_rtlog.id
    assert entry["raw"] == last_rtlog.raw
    assert entry["card_no"] == "555444"
    assert entry["reader_source"] == "acp"
    assert (entry.get("correlation_payload") or {}).get("reader_capture") is True
    assert entry["monitor_origin"] == "card_read_push"


@pytest.mark.django_db
def test_card_read_push_infers_unique_physical_controller_context():
    cache.delete("agent:last_card_read")
    cache.delete("agent:last_reader_target_context")

    Device.objects.create(
        name="Centrala VIRTUALA de TEST1",
        serial_number="SN-TEST-CTRL",
        device_type="access_panel",
        ip_address="192.168.1.100",
        port=4370,
        enabled=True,
    )
    ctrl = Device.objects.create(
        name="C3-100Pro (192.168.1.235)",
        serial_number="UNP7251400247",
        device_type="access_panel",
        ip_address="192.168.1.235",
        port=14370,
        enabled=True,
    )
    door = Door.objects.create(name="Usa ZEKO test", device=ctrl, door_number=1)

    factory = RequestFactory()
    req = factory.post(
        "/agent/api/cards/read/push/",
        data=json.dumps({"card_number": "555444", "source": "acp"}),
        content_type="application/json",
    )

    resp = card_read_push(req)
    body = json.loads(resp.content.decode("utf-8"))

    assert body["ok"] is True
    assert body["device_id"] == ctrl.id
    assert body["door_number"] == "1"
    assert body["door_pk"] == door.id

    row = DeviceRealtimeLog.objects.order_by("-id").first()
    assert row is not None
    assert row.device_id == ctrl.id
    assert ",555444,1,0,CITITOR EXTERN,acp" in str(row.raw or "")

    matched = resolve_controller_uid(device_id=ctrl.id, door_number="1")
    assert matched is not None
    assert matched.get("sniffed_card_number") == "555444"

