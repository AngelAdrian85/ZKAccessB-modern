import json

from agent.controller_capabilities import (
    build_capability_report,
    choose_runtime_driver,
    conclude_port_route_hypothesis,
    parse_probe_plcommpro_flow_output,
    resolve_port_route,
    resolve_runtime_transport,
    render_markdown_report,
)


def test_capability_report_tracks_driver_app_and_firmware_registries():
    report = build_capability_report()

    assert report["summary"]["primary_transport"] == "plcommpro_bridge"
    assert report["summary"]["secondary_transport"] == "zk_socket_driver"
    assert report["summary"]["operation_transport_strategies"] >= 4
    assert report["summary"]["firmware_web_capabilities"] >= 4

    driver_names = {f"{item['driver']}:{item['operation']}" for item in report["drivers"]}
    assert "plcommpro_bridge:get_rtlog" in driver_names
    assert "zk_socket:get_options" in driver_names

    app_names = {f"{item['area']}:{item['action']}" for item in report["app_actions"]}
    assert "personnel_sync:push_users" in app_names
    assert "personnel_sync:sync_multiple_cards_per_employee" in app_names

    ops = {item["operation"] for item in report["operation_transport_registry"]}
    assert "user-readback" in ops
    assert "user-write" in ops
    assert "option-read" in ops
    assert "rtlog-read" in ops

    fw_commands = {item["command"] for item in report["firmware_web_capabilities"]}
    assert "getdeviceinfo" in fw_commands
    assert "getdevlevel" in fw_commands

    gaps = {item["name"]: item["status"] for item in report["gaps"]}
    assert gaps["zk_socket:update_data"] == "gap"
    assert gaps["personnel_sync:sync_multiple_cards_per_employee"] == "partial"


def test_capability_report_renders_markdown_and_json():
    markdown = render_markdown_report()
    assert "# Controller Capability Matrix" in markdown
    assert "## Web UI Auth" in markdown
    assert "## Operation-Level Registry" in markdown
    assert "## Firmware Web Capabilities" in markdown
    assert "`user-readback`" in markdown

    payload = build_capability_report()
    encoded = json.dumps(payload, ensure_ascii=True)
    assert '"route_conclusion"' in encoded
    assert '"web_auth_profiles"' in encoded


def test_choose_runtime_driver_uses_operation_level_registry_priority():
    assert choose_runtime_driver("auto", operation="rtlog-read", bridge_available=True, socket_available=True, sdk_available=True) == "plcommpro"
    assert choose_runtime_driver("auto", operation="rtlog-read", bridge_available=False, socket_available=True, sdk_available=True) == "zk"
    assert choose_runtime_driver("auto", operation="user-readback", bridge_available=False, socket_available=True, sdk_available=True) == "sdk"
    assert choose_runtime_driver("auto", operation="user-write", bridge_available=False, socket_available=False, sdk_available=False) == "stub"
    assert choose_runtime_driver("zk", operation="user-write", bridge_available=True, socket_available=True, sdk_available=True) == "zk"


def test_parse_probe_output_and_route_conclusion_for_confirmed_4370():
    sample = """
Probing plcommpro flow for 192.168.1.235:4370 (protocol=TCP, timeout_ms=3000)
========================================================================
write_probe:get_device_options(DateTime): ok=True result=0 last_error=0 dll=dll-x
DateTime=2026-03-06 17:00:00
========================================================================
write_probe:set_device_options(DateTime=+30s): ok=True result=0 last_error=0 dll=dll-x
ok
========================================================================
write_probe:get_device_options(DateTime) after set: ok=True result=0 last_error=0 dll=dll-x
DateTime=2026-03-06 17:00:30
========================================================================
write_probe:data_count(user) before: ok=True result=1 last_error=0 dll=dll-x
1
========================================================================
write_probe:set_device_data(user): ok=True result=0 last_error=0 dll=dll-x
ok
========================================================================
write_probe:data_count(user) after: ok=True result=2 last_error=0 dll=dll-x
2
========================================================================
write_probe:delete_device_data(user Pin=999): ok=True result=0 last_error=0 dll=dll-x
ok
"""
    parsed = parse_probe_plcommpro_flow_output(sample)
    assert parsed["port"] == 4370
    assert parsed["datetime"]["verified"] is True
    assert parsed["user_write"]["verified"] is True

    conclusion = conclude_port_route_hypothesis(sample)
    assert conclusion["status"] == "direct_4370_confirmed"
    assert "route or forwarding dependent" in conclusion["summary"]


def test_route_conclusion_stays_pending_without_direct_probe():
    conclusion = conclude_port_route_hypothesis("")
    assert conclusion["status"] == "pending_direct_probe"
    assert conclusion["firmware_tcp_port"] == 14370


def test_capability_report_marks_direct_probe_evidence_when_artifact_is_present():
    sample = """
Probing plcommpro flow for 192.168.1.235:4370 (protocol=TCP, timeout_ms=3000)
========================================================================
write_probe:get_device_options(DateTime): ok=False result=-307 last_error=-307 dll=dll-x
connect failed
========================================================================
write_probe:data_count(user) before: ok=False result=-307 last_error=-307 dll=dll-x
connect failed
========================================================================
write_probe:set_device_data(user): ok=False result=-307 last_error=-307 dll=dll-x
connect failed
========================================================================
write_probe:data_count(user) after: ok=False result=-307 last_error=-307 dll=dll-x
connect failed
========================================================================
write_probe:delete_device_data(user Pin=999): ok=False result=-307 last_error=-307 dll=dll-x
connect failed
"""
    report = build_capability_report(direct_4370_probe_text=sample)

    evidence = next(item for item in report["port_route_evidence"] if item["evidence_id"] == "direct-lan-4370-write-probe")
    assert evidence["status"] == "verified"
    assert evidence["observed_port"] == 4370
    assert "14370 as the authoritative controller TCP port" in evidence["summary"]
    assert report["route_conclusion"]["status"] == "firmware_prefers_14370"


def test_route_resolution_prefers_firmware_tcp_port_for_c3pro_family():
    route = resolve_port_route(
        4370,
        device_name="CTRL C3-100Pro",
        hardware_version="ZMM200_C3Pro",
        firmware_version="AC Ver 4.7.8.3033 Aug 14 2023",
    )

    assert route["effective_port"] == 14370
    assert route["firmware_tcp_port"] == 14370
    assert route["candidate_ports"][:2] == [14370, 4370]


def test_runtime_transport_resolution_returns_effective_port_and_driver():
    resolved = resolve_runtime_transport(
        "auto",
        operation_class="live_monitoring",
        operation="rtlog-read",
        configured_port=4370,
        device_name="CTRL C3-100Pro",
        hardware_version="ZMM200_C3Pro",
        firmware_version="AC Ver 4.7.8.3033 Aug 14 2023",
        bridge_available=True,
        socket_available=True,
        sdk_available=True,
    )

    assert resolved["driver"] == "plcommpro"
    assert resolved["effective_port"] == 14370
    assert resolved["route_status"] == "pending_direct_probe"
