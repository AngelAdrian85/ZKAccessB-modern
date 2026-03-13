from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command

from agent.models import Device


@pytest.mark.django_db
def test_probe_live_monitor_flags_reports_active_when_all_flags_are_one(monkeypatch):
    dev = Device.objects.create(
        name="CTRL_FLAGS",
        serial_number="SN_FLAGS_1",
        ip_address="192.168.1.235",
        port=14370,
        enabled=True,
    )

    monkeypatch.setattr(
        "agent.management.commands.probe_live_monitor_flags.get_device_options",
        lambda conn, items: {
            "ok": True,
            "result": 0,
            "transport": "bridge",
            "data": "Realtime=1,RTLog=1,TransFlag=1,TransInterval=1,CardFmt=WG26,CardBitLen=26,WiegandFmtDef=WG26,WGFailedId=1,WGSiteCode=0",
        },
    )

    stdout = StringIO()
    call_command("probe_live_monitor_flags", "--device-id", str(dev.id), stdout=stdout)
    output = stdout.getvalue()

    assert "Realtime=1" in output
    assert "RTLog=1" in output
    assert "TransFlag=1" in output
    assert "live_monitoring_active=YES" in output
    assert "wiegand_mode_hint=Wiegand 26" in output
    assert "unknown_card_capture_ready=YES" in output


@pytest.mark.django_db
def test_probe_live_monitor_flags_reports_inactive_when_flag_missing(monkeypatch):
    dev = Device.objects.create(
        name="CTRL_FLAGS_OFF",
        serial_number="SN_FLAGS_2",
        ip_address="192.168.1.236",
        port=14370,
        enabled=True,
    )

    monkeypatch.setattr(
        "agent.management.commands.probe_live_monitor_flags.get_device_options",
        lambda conn, items: {
            "ok": True,
            "result": 0,
            "transport": "bridge",
            "data": "Realtime=1,RTLog=0,TransFlag=1,CardFmt=Custom,CardBitLen=37,WiegandFmtDef=,WGFailedId=0,WGSiteCode=0",
        },
    )

    stdout = StringIO()
    call_command("probe_live_monitor_flags", "--device-id", str(dev.id), stdout=stdout)
    output = stdout.getvalue()

    assert "RTLog=0" in output
    assert "live_monitoring_active=NO" in output
    assert "unknown_card_capture_ready=NO" in output
    assert "Reader Wiegand format is not clearly 26/34-bit" in output