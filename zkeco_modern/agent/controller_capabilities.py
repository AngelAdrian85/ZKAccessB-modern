from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DriverCapability:
    driver: str
    operation: str
    status: str
    implementation: str
    notes: str = ""


@dataclass(frozen=True)
class AppActionMapping:
    area: str
    action: str
    command_or_flow: str
    driver_operation: str
    controller_tables: tuple[str, ...] = ()
    coverage: str = "full"
    source: str = ""
    notes: str = ""


@dataclass(frozen=True)
class TransportStrategy:
    operation_class: str
    primary_driver: str
    fallback_drivers: tuple[str, ...] = ()
    required_operations: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class OperationTransportStrategy:
    operation: str
    operation_class: str
    primary_driver: str
    fallback_drivers: tuple[str, ...] = ()
    required_operations: tuple[str, ...] = ()
    evidence_sources: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class WebAuthProfile:
    name: str
    login_endpoint: str
    method: str
    request_fields: tuple[str, ...] = ()
    success_marker: str = ""
    notes: str = ""


@dataclass(frozen=True)
class FirmwareWebCapability:
    family: str
    firmware: str
    endpoint: str
    command: str
    auth: str
    exposed_fields: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class PortRouteEvidence:
    evidence_id: str
    source: str
    status: str
    summary: str
    observed_port: int | None = None
    notes: str = ""


@dataclass(frozen=True)
class RuntimeTransportResolution:
    requested_driver: str
    driver: str
    operation_class: str
    operation: str
    configured_port: int | None
    effective_port: int | None
    firmware_tcp_port: int | None
    route_status: str
    port_source: str
    candidate_ports: tuple[int, ...] = ()
    notes: str = ""


DRIVER_CAPABILITIES: tuple[DriverCapability, ...] = (
    DriverCapability("plcommpro_bridge", "connect", "full", "get_device_options(IPAddress)", "Fast path with optional exhaustive password/port fallback."),
    DriverCapability("plcommpro_bridge", "disconnect", "full", "stateless bridge call", "Bridge calls are request/response; disconnect is effectively a no-op wrapper."),
    DriverCapability("plcommpro_bridge", "get_options", "full", "get_device_options(items)", "Reads controller params like IPAddress, ServerAddr, ServerPort, DateTime, and identity fields."),
    DriverCapability("plcommpro_bridge", "set_options", "full", "set_device_options(items)", "Used for ADMS params, time sync, and general controller options."),
    DriverCapability("plcommpro_bridge", "get_rtlog", "full", "GetRTLog -> transaction/NewRecord -> rtlog fallback", "Best available path for real-time events and raw card numbers."),
    DriverCapability("plcommpro_bridge", "get_transaction", "full", "query_data(transaction, option=NewRecord)", "Normalizes transaction rows into RTLOG-like layout for downstream parsing."),
    DriverCapability("plcommpro_bridge", "query_data", "full", "query_data(table, fields, filter, option)", "General table reads with DLL affinity for sensitive user read-back on fragile routes."),
    DriverCapability("plcommpro_bridge", "update_data", "full", "set_device_data(table, data, option)", "Best-effort disables device for user table writes and remains the authoritative write path."),
    DriverCapability("plcommpro_bridge", "delete_data", "full", "delete_device_data(table, filter)", "Used for user/userauthorize/template cleanup flows."),
    DriverCapability("plcommpro_bridge", "data_count", "full", "data_count(table)", "Used for verification and no-op detection."),
    DriverCapability("plcommpro_bridge", "enable_device", "full", "enable_device(enable)", "Internal support mainly around safe writes."),
    DriverCapability("plcommpro_bridge", "door_control", "full", "control_device / control_normal_open / cancel_alarm / reboot", "Covers pulse open, close, normal-open state, cancel alarm, reboot."),
    DriverCapability("plcommpro_bridge", "udp_discovery", "full", "search_device_udp / modify_ip_udp", "Supports discovery and IP modification via broadcast flows."),
    DriverCapability("zk_socket", "connect", "full", "binary protocol CMD_CONNECT", "Direct TCP protocol path without DLL bridge."),
    DriverCapability("zk_socket", "disconnect", "full", "binary protocol CMD_EXIT", "Stateful socket session."),
    DriverCapability("zk_socket", "get_rtlog", "full", "CMD_GETRTLOG", "Direct real-time log read over socket."),
    DriverCapability("zk_socket", "get_transaction", "full", "CMD_GETTRANSACTION / CMD_QUERYLOG", "Can pull new or full transaction logs."),
    DriverCapability("zk_socket", "door_control", "full", "CMD_CONTROLDOOR / CMD_CANCELWARNING", "Open/close relay and cancel alarm supported."),
    DriverCapability("zk_socket", "set_options", "partial", "CMD_SETOPTIONS", "Write path exists; read/query/table-write parity is incomplete."),
    DriverCapability("zk_socket", "get_options", "partial", "CMD_GETOPTIONS + bridge fallback", "Socket-native option reads exist, but mixed-generation parity still depends on bridge fallback."),
    DriverCapability("zk_socket", "query_data", "partial", "transaction/rtlog native + bridge fallback", "Native reads cover logs; user-table verification still relies on bridge parity."),
    DriverCapability("zk_socket", "update_data", "gap", "bridge passthrough only", "No socket-native controller table write implementation yet."),
    DriverCapability("zk_socket", "delete_data", "gap", "bridge passthrough only", "No socket-native controller table delete implementation yet."),
    DriverCapability("zk_socket", "data_count", "partial", "transaction/rtlog native + bridge fallback", "Native counts exist for logs; user counts remain bridge-backed."),
)


APP_ACTIONS: tuple[AppActionMapping, ...] = (
    AppActionMapping("controller_identity", "identify_controller", "CONNECT + GET_OPTION", "connect + get_options", (), "full", "zkeco_modern/agent/modern_comm_center.py", "Reads controller reachability and identity params such as IPAddress, SerialNumber, and firmware fields."),
    AppActionMapping("controller_identity", "discover_controller", "probe_plcommpro_connect_matrix / UDP discovery", "udp_discovery", (), "partial", "zkeco_modern/agent/plcommpro_bridge.py", "Discovery exists at bridge level, but is not yet surfaced as a first-class provisioning flow across the whole UI."),
    AppActionMapping("live_monitoring", "read_live_events", "REAL_LOG", "get_rtlog", ("rtlog", "transaction"), "full", "zkeco_modern/agent/modern_comm_center.py", "Uses GetRTLog first, then transaction/NewRecord, then rtlog table fallback."),
    AppActionMapping("live_monitoring", "download_incremental_events", "DOWN_NEWLOG", "get_transaction", ("transaction",), "full", "zkeco_modern/agent/modern_comm_center.py", "Incremental event reads are persisted as DeviceEventLog and broadcast as event.batch."),
    AppActionMapping("door_control", "pulse_open_door", "DOOR_OPEN:<door>", "controldevice(time_s) -> control_normal_open fallback", (), "full", "zkeco_modern/agent/modern_comm_center.py", "Uses lock_open_duration as relay pulse when available."),
    AppActionMapping("door_control", "close_door", "DOOR_CLOSE:<door>", "controldevice -> control_normal_open fallback", (), "full", "zkeco_modern/agent/modern_comm_center.py", "Command ACK exists; physical truth still depends on RTLOG or sensor evidence."),
    AppActionMapping("door_control", "set_normal_open", "DOOR_NORMAL_OPEN:<door>", "control_normal_open -> controldevice fallback", (), "full", "zkeco_modern/agent/modern_comm_center.py"),
    AppActionMapping("door_control", "clear_normal_open", "DOOR_NORMAL_CLOSE:<door>", "control_normal_open(0) -> controldevice fallback", (), "full", "zkeco_modern/agent/modern_comm_center.py"),
    AppActionMapping("door_control", "cancel_alarm", "DOOR_CANCEL_ALARM:<door>", "cancel_alarm", (), "full", "zkeco_modern/agent/modern_comm_center.py"),
    AppActionMapping("controller_admin", "reboot_controller", "REBOOT", "controldevice(index=3)", (), "full", "zkeco_modern/agent/modern_comm_center.py"),
    AppActionMapping("controller_admin", "read_controller_params", "GET_OPTION:<items>", "get_options", (), "full", "zkeco_modern/agent/modern_comm_center.py", "Matches firmware-exposed web commands such as getdeviceinfo, getnetattr, getpushserverattr, getcommpwd, and getdatapwd."),
    AppActionMapping("controller_admin", "write_controller_params", "SET_OPTION:<items>", "set_options", (), "full", "zkeco_modern/agent/modern_comm_center.py", "Matches firmware-exposed web commands such as setnetaddrattr, setnetportattr, setpushserverattr, setcommpwd, and setdatapwd."),
    AppActionMapping("controller_admin", "sync_time", "SYNC_TIME[:timestamp]", "set_options(time=...)", (), "partial", "zkeco_modern/agent/modern_comm_center.py", "Works as a best-effort param write; a dedicated time op could be added later."),
    AppActionMapping("personnel_sync", "push_timezones", "SYNC_* flow", "update_data(timezone)", ("timezone",), "full", "zkeco_modern/agent/modern_comm_center.py", "Builds controller timezone rows from Django TimeSegment."),
    AppActionMapping("personnel_sync", "push_users", "SYNC_* flow", "update_data(user)", ("user",), "full", "zkeco_modern/agent/modern_comm_center.py", "Writes Pin, CardNo, ViceCard, Name, Group, dates, password, and super authorize."),
    AppActionMapping("personnel_sync", "push_user_authorizations", "SYNC_* flow", "update_data(userauthorize)", ("userauthorize",), "full", "zkeco_modern/agent/modern_comm_center.py", "Encodes access-level door mask and timezone relation per employee."),
    AppActionMapping("personnel_sync", "verify_user_presence", "SYNC_* verification", "data_count(user) + query_data(user)", ("user",), "full", "zkeco_modern/agent/modern_comm_center.py", "Includes no-op guard and DLL-affinity read-back verification where possible."),
    AppActionMapping("personnel_sync", "sync_departments", "embedded via Group field on user rows", "update_data(user Group=dept_id)", ("user",), "full", "zkeco_modern/agent/modern_comm_center.py", "Departments are synchronized indirectly through Group even without a dedicated department table."),
    AppActionMapping("personnel_sync", "sync_multiple_cards_per_employee", "ViceCard secondary card sync", "update_data(user CardNo,ViceCard)", ("user",), "partial", "zkeco_modern/agent/modern_comm_center.py", "Primary plus one secondary card are supported; a full arbitrary EmployeeCard set is still not modeled."),
    AppActionMapping("cleanup", "clear_personnel_data", "CLEAR_DEVICE_DATA", "delete_data(templatev10,user,usertype,userauthorize)", ("templatev10", "user", "usertype", "userauthorize"), "full", "zkeco_modern/agent/modern_comm_center.py", "Explicit no-effect guard prevents false OK on unchanged counts."),
    AppActionMapping("adms", "serve_pending_adms_commands", "ADMS:/ADMS_RAW: via /iclock/getrequest", "ADMS pull queue", (), "partial", "zkeco_modern/agent/iclock_views.py", "ADMS command serving exists, but is separate from the plcommpro transport and should be modeled as a second transport lane."),
    AppActionMapping("enrollment", "panel_user_to_card_map", "get_panel_user_card_map", "query_data(user Pin,CardNo/ViceCard)", ("user",), "full", "zkeco_modern/agent/drivers/plcommpro_bridge_driver.py", "Used to enrich missing card numbers from the actual controller table."),
    AppActionMapping("enrollment", "photos_biometrics_templates", "no active flow", "none", ("templatev10",), "gap", "zkeco_modern/agent/modern_comm_center.py", "Template cleanup exists, but no complete upload/download lifecycle for biometrics or photos is modeled."),
)


TRANSPORT_STRATEGIES: tuple[TransportStrategy, ...] = (
    TransportStrategy(
        operation_class="live_monitoring",
        primary_driver="plcommpro",
        fallback_drivers=("zk", "sdk", "socket", "stub"),
        required_operations=("get_rtlog", "get_transaction"),
        notes="Prefer bridge for mixed-generation panels; fall back to socket-native, then SDK, then probe-only modes.",
    ),
    TransportStrategy(
        operation_class="door_control",
        primary_driver="plcommpro",
        fallback_drivers=("zk", "sdk", "socket", "stub"),
        required_operations=("door_control",),
        notes="Bridge stays primary because forwarded or nonstandard ports often behave better through plcommpro bundles.",
    ),
    TransportStrategy(
        operation_class="controller_params",
        primary_driver="plcommpro",
        fallback_drivers=("sdk", "zk", "stub"),
        required_operations=("get_options", "set_options"),
        notes="Controller option reads and writes are bridge-first until full native socket parity exists.",
    ),
    TransportStrategy(
        operation_class="personnel_sync",
        primary_driver="plcommpro",
        fallback_drivers=("sdk", "stub"),
        required_operations=("query_data", "update_data", "delete_data", "data_count"),
        notes="User, userauthorize, timezone CRUD and read-back verification remain bridge-first.",
    ),
    TransportStrategy(
        operation_class="provisioning",
        primary_driver="plcommpro",
        fallback_drivers=("sdk", "zk", "stub"),
        required_operations=("connect", "get_options", "query_data", "data_count", "set_options"),
        notes="Provisioning needs the broadest coverage and deterministic DLL fallback behavior.",
    ),
)


OPERATION_TRANSPORT_STRATEGIES: tuple[OperationTransportStrategy, ...] = (
    OperationTransportStrategy(
        operation="option-read",
        operation_class="controller_params",
        primary_driver="plcommpro",
        fallback_drivers=("sdk", "zk", "stub"),
        required_operations=("get_options",),
        evidence_sources=("webui:getdeviceinfo", "webui:getnetattr", "webui:getpushserverattr"),
        notes="Bridge-first because mixed firmware and forwarded routes often require DLL-specific option affinity.",
    ),
    OperationTransportStrategy(
        operation="option-write",
        operation_class="controller_params",
        primary_driver="plcommpro",
        fallback_drivers=("sdk", "zk", "stub"),
        required_operations=("set_options",),
        evidence_sources=("webui:setnetaddrattr", "webui:setnetportattr", "webui:setpushserverattr"),
        notes="Keep writes on bridge unless a controller family is explicitly proven socket-native for the exact option set.",
    ),
    OperationTransportStrategy(
        operation="rtlog-read",
        operation_class="live_monitoring",
        primary_driver="plcommpro",
        fallback_drivers=("zk", "sdk", "socket", "stub"),
        required_operations=("get_rtlog", "get_transaction"),
        evidence_sources=("bridge:REAL_LOG", "socket:CMD_GETRTLOG", "webui:monitor.cgi"),
        notes="Socket is a valid secondary path for live logs, but bridge remains primary for mixed generations and batch normalization.",
    ),
    OperationTransportStrategy(
        operation="transaction-read",
        operation_class="live_monitoring",
        primary_driver="plcommpro",
        fallback_drivers=("zk", "sdk", "socket", "stub"),
        required_operations=("get_transaction",),
        evidence_sources=("bridge:query_data(transaction)", "socket:CMD_GETTRANSACTION"),
        notes="Use the same ordering as rtlog-read so event ingestion behavior stays consistent.",
    ),
    OperationTransportStrategy(
        operation="user-readback",
        operation_class="personnel_sync",
        primary_driver="plcommpro",
        fallback_drivers=("sdk", "stub"),
        required_operations=("query_data", "data_count"),
        evidence_sources=("bridge:user-query-dll-affinity", "sync:verify_user_presence"),
        notes="Sensitive read-back must stay bridge-first because verification stability depends on per-query DLL affinity, especially on 14370-like routes.",
    ),
    OperationTransportStrategy(
        operation="user-write",
        operation_class="personnel_sync",
        primary_driver="plcommpro",
        fallback_drivers=("sdk", "stub"),
        required_operations=("update_data", "query_data", "data_count"),
        evidence_sources=("probe:write_probe", "sync:push_users"),
        notes="Use bridge for authoritative user writes; avoid socket auto-selection until table write parity is native and verified on real panels.",
    ),
    OperationTransportStrategy(
        operation="userauth-write",
        operation_class="personnel_sync",
        primary_driver="plcommpro",
        fallback_drivers=("sdk", "stub"),
        required_operations=("update_data",),
        evidence_sources=("sync:push_user_authorizations",),
        notes="Authorization writes share the same reliability constraints as user-write.",
    ),
    OperationTransportStrategy(
        operation="timezone-write",
        operation_class="personnel_sync",
        primary_driver="plcommpro",
        fallback_drivers=("sdk", "stub"),
        required_operations=("update_data",),
        evidence_sources=("sync:push_timezones",),
        notes="Timezone provisioning is bridge-first because the same provisioning session usually performs user writes immediately after.",
    ),
    OperationTransportStrategy(
        operation="door-relay",
        operation_class="door_control",
        primary_driver="plcommpro",
        fallback_drivers=("zk", "sdk", "socket", "stub"),
        required_operations=("door_control",),
        evidence_sources=("command:DOOR_OPEN", "command:DOOR_CLOSE"),
        notes="Door relay control can tolerate socket fallback better than table CRUD, but bridge remains the safest default.",
    ),
    OperationTransportStrategy(
        operation="provision-write-probe",
        operation_class="provisioning",
        primary_driver="plcommpro",
        fallback_drivers=("sdk", "stub"),
        required_operations=("get_options", "set_options", "update_data", "query_data", "data_count"),
        evidence_sources=("probe:probe_plcommpro_flow --write-probe",),
        notes="Write-probe must mirror the authoritative write stack used in production so route verdicts are meaningful.",
    ),
)


WEB_UI_AUTH_PROFILES: tuple[WebAuthProfile, ...] = (
    WebAuthProfile(
        name="zkteco-webserver-cgi",
        login_endpoint="/cgi-bin/login.cgi",
        method="POST",
        request_fields=("-username=Base64(username)", "-userpass=MD5(password)"),
        success_marker="[Success] Login Success!",
        notes="Authenticated probing on 2026-03-06 confirmed CGI login works with browser-like XHR headers and yields a valid session for param.cgi.",
    ),
)


FIRMWARE_WEB_CAPABILITIES: tuple[FirmwareWebCapability, ...] = (
    FirmwareWebCapability(
        family="C3-100Pro / ZMM200_C3Pro",
        firmware="AC Ver 4.7.8.3033 Aug 14 2023",
        endpoint="/cgi-bin/monitor.cgi",
        command="anonymous-status",
        auth="anonymous",
        exposed_fields=("door1", "door2", "door3", "door4", "relay1", "relay2", "relay3", "relay4", "alarm1", "alarm2", "alarm3", "alarm4"),
        notes="Status endpoint is readable without session and is useful as auxiliary truth, not as the primary provisioning source.",
    ),
    FirmwareWebCapability(
        family="C3-100Pro / ZMM200_C3Pro",
        firmware="AC Ver 4.7.8.3033 Aug 14 2023",
        endpoint="/cgi-bin/param.cgi",
        command="getdeviceinfo",
        auth="session",
        exposed_fields=("IPAddress", "NetMask", "GATEIPAddress", "DNS", "TCPPort", "HTTPPort", "MAC", "IsOnlyRFMachine", "DeviceName", "SerialNumber", "Platform", "FirmVer", "MaxUserCount", "MaxFingerCount", "MaxAttLogCount", "RemainderUserCnt", "RemainderFpCnt"),
        notes="Authenticated live probe returned TCPPort=14370 and HTTPPort=443, which is direct firmware evidence for this panel family.",
    ),
    FirmwareWebCapability(
        family="C3-100Pro / ZMM200_C3Pro",
        firmware="AC Ver 4.7.8.3033 Aug 14 2023",
        endpoint="/cgi-bin/param.cgi",
        command="getpushserverattr",
        auth="session",
        exposed_fields=("WebServerIP", "WebServerPort", "WebServerURL"),
        notes="Confirms push/ADMS destination directly from firmware; this is useful for provisioning and drift detection.",
    ),
    FirmwareWebCapability(
        family="C3-100Pro / ZMM200_C3Pro",
        firmware="AC Ver 4.7.8.3033 Aug 14 2023",
        endpoint="/cgi-bin/param.cgi",
        command="getdevlevel",
        auth="session",
        exposed_fields=("PushFunOn", "MSFO", "WIFI", "IsSupportAccEncrypt"),
        notes="Provides genuine firmware ability bits. Live probe confirmed PushFunOn=1 and IsSupportAccEncrypt=1.",
    ),
    FirmwareWebCapability(
        family="C3-100Pro / ZMM200_C3Pro",
        firmware="AC Ver 4.7.8.3033 Aug 14 2023",
        endpoint="/cgi-bin/param.cgi",
        command="getcommpwd",
        auth="session",
        exposed_fields=("ComPwd",),
        notes="Live probe confirmed the controller communication password exposed by firmware matches the bridge assumptions for this panel.",
    ),
    FirmwareWebCapability(
        family="C3-100Pro / ZMM200_C3Pro",
        firmware="AC Ver 4.7.8.3033 Aug 14 2023",
        endpoint="/cgi-bin/param.cgi",
        command="getdatapwd",
        auth="session",
        exposed_fields=("AccEncryptCred",),
        notes="Firmware exposes an access-encryption credential blob, which confirms that encrypted access data is a real controller capability and not just a UI placeholder.",
    ),
    FirmwareWebCapability(
        family="C3-100Pro / ZMM200_C3Pro",
        firmware="AC Ver 4.7.8.3033 Aug 14 2023",
        endpoint="/cgi-bin/param.cgi",
        command="supported-command-scan",
        auth="session",
        exposed_fields=("getdeviceinfo", "getnetattr", "getpushserverattr", "getdevlevel", "getcommpwd", "getdatapwd", "getuserattr", "deluserattr", "getoplog", "getsystemtime", "setnetaddrattr", "setnetportattr", "setpushserverattr", "setcommpwd", "setdatapwd", "setsystemtime", "reboot", "getmasterslave", "setmasterslave"),
        notes="Commands were extracted from authenticated page and JS scanning after login, so they represent firmware-exposed CGI behavior, not a guessed API surface.",
    ),
)


PORT_ROUTE_EVIDENCE: tuple[PortRouteEvidence, ...] = (
    PortRouteEvidence(
        evidence_id="webui-firmware-port",
        source="authenticated-webui",
        status="verified",
        observed_port=14370,
        summary="Firmware-reported TCPPort is 14370 and HTTPPort is 443 on the live C3-100Pro panel.",
        notes="This is the strongest direct evidence currently available about the controller's configured SDK-style TCP service.",
    ),
    PortRouteEvidence(
        evidence_id="current-host-reachability",
        source="current-workstation",
        status="verified",
        observed_port=14370,
        summary="Current host reaches 14370 and 443, while 4370 is not reachable from this path.",
        notes="This proves a route-level difference exists, but not whether 4370 is disabled on-panel or merely blocked before reaching the panel.",
    ),
    PortRouteEvidence(
        evidence_id="direct-lan-4370-write-probe",
        source="probe_controller_direct_4370.ps1",
        status="pending",
        observed_port=4370,
        summary="Direct-LAN write_probe output has not yet been attached to the workspace for definitive comparison.",
        notes="Once captured, feed the raw output into parse_probe_plcommpro_flow_output() or build_capability_report(direct_4370_probe_text=...).",
    ),
)


def _operation_lookup() -> dict[str, OperationTransportStrategy]:
    return {item.operation: item for item in OPERATION_TRANSPORT_STRATEGIES}


def get_transport_strategy(operation_class: str) -> TransportStrategy:
    op = str(operation_class or "live_monitoring").strip().lower() or "live_monitoring"
    for strategy in TRANSPORT_STRATEGIES:
        if strategy.operation_class == op:
            return strategy
    return TRANSPORT_STRATEGIES[0]


def get_operation_transport_strategy(operation: str, *, operation_class: str = "") -> OperationTransportStrategy:
    op = str(operation or "").strip().lower()
    if op:
        match = _operation_lookup().get(op)
        if match is not None:
            return match
    if operation_class:
        broad = get_transport_strategy(operation_class)
        return OperationTransportStrategy(
            operation=op or operation_class,
            operation_class=broad.operation_class,
            primary_driver=broad.primary_driver,
            fallback_drivers=broad.fallback_drivers,
            required_operations=broad.required_operations,
            evidence_sources=(),
            notes=broad.notes,
        )
    first = OPERATION_TRANSPORT_STRATEGIES[0]
    return first


def _normalize_port(value: Any) -> int | None:
    try:
        port = int(value)
    except Exception:
        return None
    if port <= 0 or port > 65535:
        return None
    return port


def infer_firmware_tcp_port(
    *,
    option_pairs: dict[str, Any] | None = None,
    device_name: str = "",
    hardware_version: str = "",
    firmware_version: str = "",
) -> int | None:
    options = dict(option_pairs or {})
    option_port = _normalize_port(options.get("TCPPort"))
    if option_port is not None:
        return option_port

    markers = " ".join(
        [
            str(device_name or "").upper(),
            str(hardware_version or "").upper(),
            str(firmware_version or "").upper(),
        ]
    )
    if any(marker in markers for marker in ("C3-100PRO", "ZMM200_C3PRO", "AC VER 4.7.8.3033")):
        return 14370
    return None


def resolve_port_route(
    configured_port: int | None,
    *,
    option_pairs: dict[str, Any] | None = None,
    device_name: str = "",
    hardware_version: str = "",
    firmware_version: str = "",
    direct_4370_probe_text: str = "",
) -> dict[str, Any]:
    configured = _normalize_port(configured_port)
    firmware_tcp_port = infer_firmware_tcp_port(
        option_pairs=option_pairs,
        device_name=device_name,
        hardware_version=hardware_version,
        firmware_version=firmware_version,
    )
    route = conclude_port_route_hypothesis(direct_4370_probe_text)
    route_status = str(route.get("status") or "pending_direct_probe")
    effective_port = configured or firmware_tcp_port or 4370
    port_source = "configured" if configured is not None else ("firmware" if firmware_tcp_port is not None else "default")
    notes = ""

    if firmware_tcp_port is not None and route_status in {"pending_direct_probe", "firmware_prefers_14370"}:
        if configured != firmware_tcp_port:
            effective_port = firmware_tcp_port
            port_source = "firmware"
            notes = "Firmware-advertised TCPPort is preferred until a direct 4370 write-probe proves equivalent semantics."
    elif route_status == "direct_4370_confirmed" and configured is not None:
        effective_port = configured
        port_source = "configured"

    candidates: list[int] = []
    if effective_port is not None:
        candidates.append(effective_port)
    if route_status == "direct_4370_confirmed":
        candidates.append(4370)
    if configured is not None:
        candidates.append(configured)
    if firmware_tcp_port is not None:
        candidates.append(firmware_tcp_port)
    candidates.append(4370)

    seen: set[int] = set()
    ordered: list[int] = []
    for port in candidates:
        normalized = _normalize_port(port)
        if normalized is None or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)

    return {
        "configured_port": configured,
        "effective_port": effective_port,
        "firmware_tcp_port": firmware_tcp_port,
        "route_status": route_status,
        "route_summary": route.get("summary") or "",
        "port_source": port_source,
        "candidate_ports": ordered,
        "notes": notes,
    }


def _choose_driver_from_strategy(
    requested_driver: str,
    *,
    operation_class: str,
    operation: str | None,
    bridge_available: bool,
    socket_available: bool,
    sdk_available: bool,
) -> str:
    requested = str(requested_driver or "auto").strip().lower() or "auto"
    explicit = {"stub", "socket", "zk", "plcommpro", "sdk"}
    if requested in explicit and requested != "auto":
        return requested

    if operation:
        strategy = get_operation_transport_strategy(operation, operation_class=operation_class)
    else:
        broad = get_transport_strategy(operation_class)
        strategy = OperationTransportStrategy(
            operation=operation_class,
            operation_class=broad.operation_class,
            primary_driver=broad.primary_driver,
            fallback_drivers=broad.fallback_drivers,
            required_operations=broad.required_operations,
            evidence_sources=(),
            notes=broad.notes,
        )

    availability = {
        "plcommpro": bool(bridge_available),
        "zk": bool(socket_available),
        "sdk": bool(sdk_available),
        "socket": True,
        "stub": True,
    }
    ordered = (strategy.primary_driver,) + tuple(strategy.fallback_drivers)
    for driver in ordered:
        if availability.get(driver, False):
            return driver
    return "stub"


def resolve_runtime_transport(
    requested_driver: str,
    *,
    operation_class: str = "live_monitoring",
    operation: str | None = None,
    configured_port: int | None = None,
    option_pairs: dict[str, Any] | None = None,
    device_name: str = "",
    hardware_version: str = "",
    firmware_version: str = "",
    direct_4370_probe_text: str = "",
    bridge_available: bool = False,
    socket_available: bool = True,
    sdk_available: bool = False,
) -> dict[str, Any]:
    requested = str(requested_driver or "auto").strip().lower() or "auto"
    driver = _choose_driver_from_strategy(
        requested,
        operation_class=operation_class,
        operation=operation,
        bridge_available=bridge_available,
        socket_available=socket_available,
        sdk_available=sdk_available,
    )
    route = resolve_port_route(
        configured_port,
        option_pairs=option_pairs,
        device_name=device_name,
        hardware_version=hardware_version,
        firmware_version=firmware_version,
        direct_4370_probe_text=direct_4370_probe_text,
    )
    notes = str(route.get("notes") or "")

    if requested == "auto" and route.get("port_source") == "firmware" and bridge_available and driver in {"zk", "socket"}:
        driver = "plcommpro"
        notes = (notes + " Auto driver selection was pinned to plcommpro because firmware route evidence overrides the configured port.").strip()

    resolution = RuntimeTransportResolution(
        requested_driver=requested,
        driver=driver,
        operation_class=str(operation_class or "live_monitoring"),
        operation=str(operation or ""),
        configured_port=route.get("configured_port"),
        effective_port=route.get("effective_port"),
        firmware_tcp_port=route.get("firmware_tcp_port"),
        route_status=str(route.get("route_status") or "pending_direct_probe"),
        port_source=str(route.get("port_source") or "configured"),
        candidate_ports=tuple(route.get("candidate_ports") or ()),
        notes=notes,
    )
    return asdict(resolution)


def choose_runtime_driver(
    requested_driver: str,
    *,
    operation_class: str = "live_monitoring",
    operation: str | None = None,
    bridge_available: bool = False,
    socket_available: bool = True,
    sdk_available: bool = False,
) -> str:
    resolved = resolve_runtime_transport(
        requested_driver,
        operation_class=operation_class,
        operation=operation,
        bridge_available=bridge_available,
        socket_available=socket_available,
        sdk_available=sdk_available,
    )
    return str(resolved.get("driver") or "stub")


def _parse_dump_sections(text: str) -> dict[str, dict[str, Any]]:
    sections: dict[str, dict[str, Any]] = {}
    current_title = ""
    body: list[str] = []
    for raw_line in str(text or "").splitlines():
        line = raw_line.rstrip("\r")
        stripped = line.strip()
        if stripped.startswith("="):
            if current_title:
                if current_title not in sections:
                    sections[current_title] = {}
                sections[current_title]["body"] = "\n".join(body).strip()
            current_title = ""
            body = []
            continue
        if ": ok=" in stripped and not current_title:
            title = stripped.split(": ok=", 1)[0].strip()
            current_title = title
            result_match = re.search(r"result=([^\s]+)", stripped)
            ok_match = re.search(r"ok=(True|False)", stripped)
            last_error_match = re.search(r"last_error=([^\s]+)", stripped)
            sections[current_title] = {
                "ok": bool(ok_match and ok_match.group(1) == "True"),
                "result": result_match.group(1) if result_match else "",
                "last_error": last_error_match.group(1) if last_error_match else "",
                "body": "",
            }
            body = []
            continue
        if current_title:
            body.append(stripped)
    if current_title and current_title in sections:
        sections[current_title]["body"] = "\n".join(body).strip()
    return sections


def _extract_first_int(text: str) -> int | None:
    match = re.search(r"-?\d+", str(text or ""))
    if not match:
        return None
    try:
        return int(match.group(0))
    except Exception:
        return None


def parse_probe_plcommpro_flow_output(text: str) -> dict[str, Any]:
    payload = str(text or "")
    sections = _parse_dump_sections(payload)
    port_match = re.search(r"Probing plcommpro flow for\s+[^:]+:(\d+)", payload)
    out: dict[str, Any] = {
        "port": int(port_match.group(1)) if port_match else None,
        "datetime": {"write_attempted": False, "before": "", "after": "", "write_result": "", "verified": False},
        "user_write": {
            "write_attempted": False,
            "before_count": None,
            "after_count": None,
            "write_result": "",
            "verify_preview": "",
            "cleanup_result": "",
            "verified": False,
        },
    }

    dt_before = sections.get("write_probe:get_device_options(DateTime)", {})
    dt_after = sections.get("write_probe:get_device_options(DateTime) after set", {})
    dt_write = sections.get("write_probe:set_device_options(DateTime=+30)", {})
    if not dt_write:
        dt_write = sections.get("write_probe:set_device_options(DateTime=+30s)", {})
    if dt_before or dt_after or dt_write:
        out["datetime"]["write_attempted"] = True
        before_match = re.search(r"DateTime=([^,\r\n]+)", str(dt_before.get("body") or ""))
        after_match = re.search(r"DateTime=([^,\r\n]+)", str(dt_after.get("body") or ""))
        out["datetime"]["before"] = before_match.group(1).strip() if before_match else ""
        out["datetime"]["after"] = after_match.group(1).strip() if after_match else ""
        out["datetime"]["write_result"] = str(dt_write.get("result") or "")
        out["datetime"]["verified"] = bool(out["datetime"]["before"] and out["datetime"]["after"] and out["datetime"]["before"] != out["datetime"]["after"])

    user_before = sections.get("write_probe:data_count(user) before", {})
    user_after = sections.get("write_probe:data_count(user) after", {})
    user_write = sections.get("write_probe:set_device_data(user)", {})
    user_cleanup = sections.get("write_probe:delete_device_data(user Pin=999)", {})
    if user_before or user_after or user_write or user_cleanup:
        out["user_write"]["write_attempted"] = True
        out["user_write"]["before_count"] = _extract_first_int(str(user_before.get("body") or ""))
        out["user_write"]["after_count"] = _extract_first_int(str(user_after.get("body") or ""))
        out["user_write"]["write_result"] = str(user_write.get("result") or "")
        out["user_write"]["cleanup_result"] = str(user_cleanup.get("result") or "")
        out["user_write"]["verify_preview"] = str(user_write.get("body") or "")[:240]
        before_count = out["user_write"]["before_count"]
        after_count = out["user_write"]["after_count"]
        out["user_write"]["verified"] = bool(before_count is not None and after_count is not None and after_count > before_count)
    return out


def conclude_port_route_hypothesis(direct_4370_probe_text: str = "") -> dict[str, Any]:
    base = {
        "firmware_tcp_port": 14370,
        "configured_http_port": 443,
        "status": "pending_direct_probe",
        "summary": "Firmware and current-route evidence favor TCPPort=14370, but direct-LAN 4370 write-probe output is still required for a definitive route verdict.",
        "direct_probe": None,
    }
    probe_text = str(direct_4370_probe_text or "").strip()
    if not probe_text:
        return base

    parsed = parse_probe_plcommpro_flow_output(probe_text)
    base["direct_probe"] = parsed
    dt_verified = bool(parsed.get("datetime", {}).get("verified"))
    user_verified = bool(parsed.get("user_write", {}).get("verified"))
    port = parsed.get("port")

    if port == 4370 and (dt_verified or user_verified):
        base["status"] = "direct_4370_confirmed"
        base["summary"] = (
            "Direct-LAN probe confirmed active write semantics on 4370. For this panel, 14370 is the firmware-advertised TCP service, "
            "but 4370 remains a real native path when reached locally; any mismatch seen from the current host is therefore route or forwarding dependent."
        )
        return base

    if port == 4370 and parsed.get("datetime", {}).get("write_attempted"):
        base["status"] = "firmware_prefers_14370"
        base["summary"] = (
            "Direct-LAN probe on 4370 did not prove writable controller semantics, while authenticated firmware data explicitly reports TCPPort=14370. "
            "This strongly supports treating 14370 as the authoritative controller TCP port for this panel."
        )
        return base

    base["status"] = "direct_probe_unparsed"
    base["summary"] = "A direct-LAN artifact was provided, but it did not match the expected probe_plcommpro_flow output shape closely enough for an automatic verdict."
    return base


def build_capability_report(*, direct_4370_probe_text: str = "") -> dict[str, Any]:
    drivers = [asdict(item) for item in DRIVER_CAPABILITIES]
    actions = [
        {
            **asdict(item),
            "controller_tables": list(item.controller_tables),
        }
        for item in APP_ACTIONS
    ]
    operation_registry = [asdict(item) for item in OPERATION_TRANSPORT_STRATEGIES]
    firmware_registry = [
        {
            **asdict(item),
            "exposed_fields": list(item.exposed_fields),
        }
        for item in FIRMWARE_WEB_CAPABILITIES
    ]
    auth_profiles = [
        {
            **asdict(item),
            "request_fields": list(item.request_fields),
        }
        for item in WEB_UI_AUTH_PROFILES
    ]

    gaps = []
    for item in DRIVER_CAPABILITIES:
        if item.status in {"gap", "partial"}:
            gaps.append(
                {
                    "type": "driver",
                    "name": f"{item.driver}:{item.operation}",
                    "status": item.status,
                    "notes": item.notes,
                }
            )
    for item in APP_ACTIONS:
        if item.coverage in {"gap", "partial"}:
            gaps.append(
                {
                    "type": "app_action",
                    "name": f"{item.area}:{item.action}",
                    "status": item.coverage,
                    "notes": item.notes,
                }
            )

    recommended_next_steps = [
        "Promote this capability registry to the source of truth for every controller-facing feature before adding more commands.",
        "Keep bridge-first selection for user-write and user-readback until direct-LAN 4370 evidence proves native parity for the exact controller family in use.",
        "Feed the raw output from probe_controller_direct_4370.ps1 into build_capability_report(direct_4370_probe_text=...) to turn the current pending route hypothesis into a definitive verdict.",
        "Extend firmware-aware rules by mapping additional authenticated param.cgi commands such as getuserattr and getoplog to explicit app features.",
        "Implement full table parity in zk_socket_driver for query/update/delete/count/get_options so the socket transport can become a real secondary bridge rather than a partial log path.",
    ]

    route_conclusion = conclude_port_route_hypothesis(direct_4370_probe_text)
    port_route_evidence = [asdict(item) for item in PORT_ROUTE_EVIDENCE]
    for item in port_route_evidence:
        if item.get("evidence_id") != "direct-lan-4370-write-probe":
            continue
        status = str(route_conclusion.get("status") or "pending_direct_probe")
        if status == "pending_direct_probe":
            break
        item["status"] = "verified" if status in {"firmware_prefers_14370", "direct_4370_confirmed"} else "provided"
        item["summary"] = str(route_conclusion.get("summary") or item.get("summary") or "")
        direct_probe = route_conclusion.get("direct_probe") or {}
        item["observed_port"] = direct_probe.get("port") or item.get("observed_port")
        break

    return {
        "summary": {
            "primary_transport": "plcommpro_bridge",
            "secondary_transport": "zk_socket_driver",
            "app_actions": len(actions),
            "driver_capabilities": len(drivers),
            "transport_strategies": len(TRANSPORT_STRATEGIES),
            "operation_transport_strategies": len(OPERATION_TRANSPORT_STRATEGIES),
            "firmware_web_capabilities": len(FIRMWARE_WEB_CAPABILITIES),
            "gaps_or_partials": len(gaps),
        },
        "web_auth_profiles": auth_profiles,
        "drivers": drivers,
        "app_actions": actions,
        "transport_registry": [asdict(item) for item in TRANSPORT_STRATEGIES],
        "operation_transport_registry": operation_registry,
        "firmware_web_capabilities": firmware_registry,
        "port_route_evidence": port_route_evidence,
        "route_conclusion": route_conclusion,
        "gaps": gaps,
        "recommended_next_steps": recommended_next_steps,
    }


def render_markdown_report(*, direct_4370_probe_text: str = "") -> str:
    report = build_capability_report(direct_4370_probe_text=direct_4370_probe_text)
    lines: list[str] = []
    lines.append("# Controller Capability Matrix")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    summary = report["summary"]
    lines.append(f"- Primary transport: `{summary['primary_transport']}`")
    lines.append(f"- Secondary transport: `{summary['secondary_transport']}`")
    lines.append(f"- Driver capabilities tracked: `{summary['driver_capabilities']}`")
    lines.append(f"- App actions tracked: `{summary['app_actions']}`")
    lines.append(f"- Broad transport strategies tracked: `{summary['transport_strategies']}`")
    lines.append(f"- Operation-level strategies tracked: `{summary['operation_transport_strategies']}`")
    lines.append(f"- Firmware web capabilities tracked: `{summary['firmware_web_capabilities']}`")
    lines.append(f"- Gaps or partials: `{summary['gaps_or_partials']}`")
    lines.append("")
    lines.append("## Web UI Auth")
    lines.append("")
    for item in report["web_auth_profiles"]:
        fields = ", ".join(f"`{f}`" for f in item["request_fields"]) if item["request_fields"] else "-"
        lines.append(f"- `{item['name']}`: `{item['method']}` `{item['login_endpoint']}` using {fields}; success marker `{item['success_marker']}`. {item['notes']}")
    lines.append("")
    lines.append("## Executable Transport Registry")
    lines.append("")
    lines.append("| Operation Class | Primary | Fallbacks | Required Ops | Notes |")
    lines.append("| --- | --- | --- | --- | --- |")
    for item in report["transport_registry"]:
        fallbacks = ", ".join(f"`{d}`" for d in item["fallback_drivers"]) if item["fallback_drivers"] else "-"
        required = ", ".join(f"`{d}`" for d in item["required_operations"]) if item["required_operations"] else "-"
        lines.append(
            f"| `{item['operation_class']}` | `{item['primary_driver']}` | {fallbacks} | {required} | {item['notes']} |"
        )
    lines.append("")
    lines.append("## Operation-Level Registry")
    lines.append("")
    lines.append("| Operation | Class | Primary | Fallbacks | Required Ops | Evidence | Notes |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for item in report["operation_transport_registry"]:
        fallbacks = ", ".join(f"`{d}`" for d in item["fallback_drivers"]) if item["fallback_drivers"] else "-"
        required = ", ".join(f"`{d}`" for d in item["required_operations"]) if item["required_operations"] else "-"
        evidence = ", ".join(f"`{d}`" for d in item["evidence_sources"]) if item["evidence_sources"] else "-"
        lines.append(
            f"| `{item['operation']}` | `{item['operation_class']}` | `{item['primary_driver']}` | {fallbacks} | {required} | {evidence} | {item['notes']} |"
        )
    lines.append("")
    lines.append("## Firmware Web Capabilities")
    lines.append("")
    lines.append("| Family | Firmware | Endpoint | Command | Auth | Exposed Fields | Notes |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for item in report["firmware_web_capabilities"]:
        fields = ", ".join(f"`{field}`" for field in item["exposed_fields"]) if item["exposed_fields"] else "-"
        lines.append(
            f"| `{item['family']}` | `{item['firmware']}` | `{item['endpoint']}` | `{item['command']}` | `{item['auth']}` | {fields} | {item['notes']} |"
        )
    lines.append("")
    lines.append("## Port Route Evidence")
    lines.append("")
    for item in report["port_route_evidence"]:
        port_txt = f" port=`{item['observed_port']}`" if item.get("observed_port") else ""
        lines.append(f"- `{item['evidence_id']}` [{item['status']}] from `{item['source']}`:{port_txt} {item['summary']} {item['notes']}")
    lines.append("")
    lines.append("## Route Conclusion")
    lines.append("")
    route = report["route_conclusion"]
    lines.append(f"- status: `{route['status']}`")
    lines.append(f"- summary: {route['summary']}")
    lines.append("")
    lines.append("## Driver Capabilities")
    lines.append("")
    lines.append("| Driver | Operation | Status | Implementation | Notes |")
    lines.append("| --- | --- | --- | --- | --- |")
    for item in report["drivers"]:
        lines.append(
            f"| `{item['driver']}` | `{item['operation']}` | `{item['status']}` | `{item['implementation']}` | {item['notes']} |"
        )
    lines.append("")
    lines.append("## App Action Mapping")
    lines.append("")
    lines.append("| Area | Action | Flow | Driver Operation | Tables | Coverage | Source | Notes |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for item in report["app_actions"]:
        tables = ", ".join(f"`{t}`" for t in item["controller_tables"]) if item["controller_tables"] else "-"
        lines.append(
            f"| `{item['area']}` | `{item['action']}` | `{item['command_or_flow']}` | `{item['driver_operation']}` | {tables} | `{item['coverage']}` | `{item['source']}` | {item['notes']} |"
        )
    lines.append("")
    lines.append("## Gaps And Partials")
    lines.append("")
    for gap in report["gaps"]:
        lines.append(f"- `{gap['type']}` `{gap['name']}`: `{gap['status']}` - {gap['notes']}")
    lines.append("")
    lines.append("## Recommended Next Steps")
    lines.append("")
    for step in report["recommended_next_steps"]:
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)
