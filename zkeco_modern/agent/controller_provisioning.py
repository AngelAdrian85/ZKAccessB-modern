from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

from django.db import IntegrityError

from .controller_capabilities import resolve_port_route
from .controller_decoders import parse_option_pairs
from .door_provisioning import ensure_controller_doors
from .drivers.zk_socket_driver import ZKTechSocketDriver
from .models import Device, DeviceStatus
from .plcommpro_bridge import (
    PlcommproConnInfo,
    data_count,
    delete_device_data,
    get_device_options,
    query_data,
    search_device_udp,
    set_device_data,
    set_device_options,
)


DEFAULT_OPTION_ITEMS = (
    "IPAddress,NetMask,GATEIPAddress,~SerialNumber,DeviceName,Product,DateTime,ServerAddr,ServerPort,Realtime,RTLog"
)
DEFAULT_TABLES = ("user", "userauthorize", "timezone", "transaction", "rtlog", "templatev10", "usertype")


def _unique_ports(values: list[Any]) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for value in values:
        try:
            port = int(value)
        except Exception:
            continue
        if port <= 0 or port > 65535 or port in seen:
            continue
        seen.add(port)
        out.append(port)
    return out


@dataclass(frozen=True)
class ProvisionTarget:
    ip: str
    port: int = 4370
    password: str = ""
    timeout_ms: int = 3000
    protocol: str = "TCP"

    def conn(self) -> PlcommproConnInfo:
        return PlcommproConnInfo(
            ipaddress=str(self.ip or "").strip(),
            ip_port=int(self.port or 4370),
            password=str(self.password or ""),
            timeout=int(self.timeout_ms or 3000),
            protocol=str(self.protocol or "TCP").strip().upper() or "TCP",
        )


def _target_with_route(target: ProvisionTarget, option_pairs: dict[str, str] | None = None) -> tuple[ProvisionTarget, dict[str, Any]]:
    route = resolve_port_route(
        target.port,
        option_pairs=option_pairs,
    )
    effective_port = int(route.get("effective_port") or target.port or 4370)
    if effective_port == int(target.port or 4370):
        return target, route
    return (
        ProvisionTarget(
            ip=target.ip,
            port=effective_port,
            password=target.password,
            timeout_ms=target.timeout_ms,
            protocol=target.protocol,
        ),
        route,
    )


def _candidate_option_targets(target: ProvisionTarget) -> list[ProvisionTarget]:
    route = resolve_port_route(target.port)
    ports = _unique_ports(list(route.get("candidate_ports") or []) + [target.port, 14370, 4370, 4371, 4372])
    return [
        ProvisionTarget(
            ip=target.ip,
            port=port,
            password=target.password,
            timeout_ms=target.timeout_ms,
            protocol=target.protocol,
        )
        for port in ports
    ]


def parse_search_device_output(raw: str) -> list[dict[str, Any]]:
    raw = (raw or "").replace("\x00", "").strip()
    if not raw:
        return []
    records = [r.strip() for r in re.split(r"[\r\n]+", raw) if r.strip()]
    if len(records) == 1 and raw.count("=") > 4 and "," in raw and raw.count("IPAddress=") > 1:
        records = [r.strip() for r in re.split(r"(?=\b(?:IP|IPAddress|MAC|SN)=)", raw) if r.strip()]

    key_map = {
        "ip": "ip",
        "ipaddress": "ip",
        "sn": "serial_number",
        "serial": "serial_number",
        "serialnumber": "serial_number",
        "mac": "mac",
        "devicename": "device_name",
        "device": "device_name",
        "product": "product",
        "model": "model",
        "devicetype": "model",
        "devicetypename": "model",
        "deviceclass": "model",
        "productname": "model",
        "devicemodel": "model",
        "fwversion": "fw_version",
        "firmware": "fw_version",
        "commport": "port",
        "port": "port",
        "netmask": "netmask",
        "gateipaddress": "gateway",
        "gateway": "gateway",
    }

    out: list[dict[str, Any]] = []
    for rec in records:
        normalized: dict[str, Any] = {"raw": rec}
        extras: dict[str, str] = {}
        parts = [p.strip() for p in re.split(r"[,;\t]+", rec) if p.strip()]
        for part in parts:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            key = (key or "").strip()
            value = (value or "").strip()
            if not key:
                continue
            mapped = key_map.get(key.lower())
            if mapped == "port":
                try:
                    normalized[mapped] = int(value or "0") or None
                except Exception:
                    normalized[mapped] = None
            elif mapped:
                normalized[mapped] = value
            else:
                extras[key] = value
        if extras:
            normalized["extra"] = extras
        if not str(normalized.get("model") or "").strip() and str(normalized.get("product") or "").strip():
            normalized["model"] = str(normalized.get("product") or "").strip()
        out.append(normalized)
    return out

def discover_controller(base: str = "") -> dict[str, Any]:
    addr = None
    if str(base or "").strip():
        addr = f"{str(base).strip()}.255"
    resp = search_device_udp(address=addr)
    return {
        "ok": bool(resp.get("ok")),
        "raw": str(resp.get("data") or ""),
        "devices": parse_search_device_output(str(resp.get("data") or "")),
        "result": resp.get("result"),
        "last_error": resp.get("last_error"),
    }


def _native_socket_get_options(target: ProvisionTarget, items: str) -> dict[str, Any]:
    if str(target.protocol or "TCP").strip().upper() != "TCP":
        return {"result": -1, "ok": False, "error": "socket-native-tcp-only", "transport": "socket-native"}
    effective_target, route = _target_with_route(target)
    driver = ZKTechSocketDriver.from_connection_info(ip=effective_target.ip, port=effective_target.port, password=effective_target.password)
    driver.timeout = max(1.0, float(int(target.timeout_ms or 3000)) / 1000.0)
    conn_resp = driver.connect()
    if int(conn_resp.get("result", -1) or -1) < 0:
        return {
            "result": int(conn_resp.get("result", -1) or -1),
            "ok": False,
            "error": conn_resp.get("error"),
            "transport": "socket-native",
        }
    try:
        resp = dict(driver.get_options(items) or {})
        resp["transport"] = resp.get("transport") or "socket-native"
        resp["ok"] = bool(resp.get("ok")) or bool(str(resp.get("data") or "").strip())
        resp["effective_port"] = int(route.get("effective_port") or effective_target.port)
        return resp
    finally:
        driver.disconnect()


def _read_controller_options(target: ProvisionTarget, items: str) -> dict[str, Any]:
    requested_items = [part.strip() for part in str(items or "").split(",") if part.strip()]
    attempts: list[dict[str, Any]] = []
    primary: dict[str, Any] | None = None
    selected_target = target
    for idx, candidate in enumerate(_candidate_option_targets(target)):
        attempt = dict(get_device_options(candidate.conn(), items) or {})
        attempt.setdefault("transport", "bridge")
        attempt["requested_port"] = int(target.port or 4370)
        attempt["resolved_port"] = int(candidate.port or 4370)
        primary_data = bool(str(attempt.get("data") or "").strip())
        attempt["ok"] = bool(attempt.get("ok")) or (int(attempt.get("result", -1) or -1) >= 0 and primary_data)
        attempts.append(attempt)
        if idx == 0:
            primary = attempt
        if attempt["ok"]:
            selected_target = candidate
            if candidate.port != target.port:
                attempt["fallback_from_port"] = int(target.port or 4370)
            return attempt

    primary = dict(primary or {"result": -1, "ok": False, "data": "", "transport": "bridge"})
    primary["bridge_attempts"] = attempts

    if len(requested_items) > 1:
        merged_pairs: dict[str, str] = {}
        transports: list[str] = []
        resolved_ports: list[int] = []
        for item in requested_items:
            single = _read_controller_options(target, item)
            if not bool(single.get("ok")):
                continue
            merged_pairs.update(parse_option_pairs(str(single.get("data") or "")))
            transport = str(single.get("transport") or "").strip()
            if transport:
                transports.append(transport)
            try:
                resolved_ports.append(int(single.get("resolved_port") or 0))
            except Exception:
                pass
        if merged_pairs:
            ordered_pairs = [f"{item}={merged_pairs[item]}" for item in requested_items if item in merged_pairs]
            return {
                "result": 0,
                "ok": True,
                "data": ",".join(ordered_pairs),
                "transport": "+".join(sorted(set(transports))) or "bridge-item-fallback",
                "partial": len(merged_pairs) < len(requested_items),
                "requested_port": int(target.port or 4370),
                "resolved_port": resolved_ports[0] if resolved_ports else int(target.port or 4370),
            }

    for candidate in _candidate_option_targets(target):
        fallback = _native_socket_get_options(candidate, items)
        fallback["requested_port"] = int(target.port or 4370)
        fallback["resolved_port"] = int(candidate.port or 4370)
        if bool(fallback.get("ok")):
            fallback["fallback_from"] = primary.get("transport")
            if candidate.port != target.port:
                fallback["fallback_from_port"] = int(target.port or 4370)
            return fallback

    if 'fallback' in locals() and fallback:
        primary["socket_fallback"] = fallback
    return primary


def _write_controller_options(target: ProvisionTarget, items: str) -> dict[str, Any]:
    primary = dict(set_device_options(target.conn(), items) or {})
    primary.setdefault("transport", "bridge")
    if int(primary.get("result", -1) or -1) >= 0:
        return primary

    if str(target.protocol or "TCP").strip().upper() != "TCP":
        return primary
    driver = ZKTechSocketDriver.from_connection_info(ip=target.ip, port=target.port, password=target.password)
    driver.timeout = max(1.0, float(int(target.timeout_ms or 3000)) / 1000.0)
    conn_resp = driver.connect()
    if int(conn_resp.get("result", -1) or -1) < 0:
        primary["socket_fallback"] = {
            "result": int(conn_resp.get("result", -1) or -1),
            "error": conn_resp.get("error"),
            "transport": "socket-native",
        }
        return primary
    try:
        fallback = dict(driver.set_options(items) or {})
        fallback["transport"] = fallback.get("transport") or "socket-native"
        if int(fallback.get("result", -1) or -1) >= 0:
            fallback["fallback_from"] = primary.get("transport")
            return fallback
        primary["socket_fallback"] = fallback
        return primary
    finally:
        driver.disconnect()


def snapshot_controller(target: ProvisionTarget, *, option_items: str = DEFAULT_OPTION_ITEMS, table_names: tuple[str, ...] = DEFAULT_TABLES) -> dict[str, Any]:
    opt_resp = _read_controller_options(target, option_items)
    options = parse_option_pairs(str(opt_resp.get("data") or "")) if opt_resp.get("ok") else {}
    option_port = int(opt_resp.get("resolved_port") or target.port or 4370)
    option_target = ProvisionTarget(
        ip=target.ip,
        port=option_port,
        password=target.password,
        timeout_ms=target.timeout_ms,
        protocol=target.protocol,
    )
    effective_target, route = _target_with_route(option_target, options)
    conn = effective_target.conn()

    tables: list[dict[str, Any]] = []
    for table in table_names:
        count_resp = data_count(conn, table)
        query_resp = query_data(conn, table=table, fields="*", option="NewRecord" if table == "transaction" else "")
        preview = str(query_resp.get("data") or "")
        lines = [ln for ln in preview.replace("\x00", "").split("\r\n") if str(ln or "").strip()]
        tables.append(
            {
                "table": table,
                "count_result": count_resp.get("result"),
                "query_result": query_resp.get("result"),
                "supported": int(count_resp.get("result", -1) or -1) >= 0 or int(query_resp.get("result", -1) or -1) >= 0,
                "preview": "\r\n".join(lines[:5]),
            }
        )

    identify = {
        "ip": options.get("IPAddress") or target.ip,
        "serial_number": options.get("~SerialNumber") or "",
        "device_name": options.get("DeviceName") or "",
        "product": options.get("Product") or options.get("Platform") or "",
        "netmask": options.get("NetMask") or "",
        "gateway": options.get("GATEIPAddress") or "",
    }
    return {
        "target": {"ip": effective_target.ip, "port": effective_target.port, "configured_port": target.port, "timeout_ms": target.timeout_ms, "protocol": target.protocol},
        "identify": identify,
        "options": options,
        "options_ok": bool(opt_resp.get("ok")),
        "option_result": opt_resp.get("result"),
        "option_transport": opt_resp.get("transport"),
        "option_requested_port": opt_resp.get("requested_port"),
        "option_resolved_port": opt_resp.get("resolved_port"),
        "route_resolution": route,
        "tables": tables,
    }


def probe_writeability(target: ProvisionTarget) -> dict[str, Any]:
    conn = target.conn()
    report: dict[str, Any] = {"datetime": {"supported": False}, "user_write": {"supported": False}}

    dt_resp = _read_controller_options(target, "DateTime")
    dt_pairs = parse_option_pairs(str(dt_resp.get("data") or "")) if dt_resp.get("ok") else {}
    dt_value = str(dt_pairs.get("DateTime") or "").strip()
    if dt_value:
        report["datetime"]["before"] = dt_value
        report["datetime"]["supported"] = True
        report["datetime"]["read_transport"] = dt_resp.get("transport")
        restore_value = dt_value
        try:
            if re.fullmatch(r"\d+", dt_value):
                target_value = str(int(dt_value) + 30)
            else:
                target_value = (datetime.strptime(dt_value, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=30)).strftime("%Y-%m-%d %H:%M:%S")
            set_resp = _write_controller_options(target, f"DateTime={target_value}")
            verify_resp = _read_controller_options(target, "DateTime")
            _write_controller_options(target, f"DateTime={restore_value}")
            report["datetime"].update(
                {
                    "write_result": set_resp.get("result"),
                    "write_transport": set_resp.get("transport"),
                    "verify": parse_option_pairs(str(verify_resp.get("data") or "")).get("DateTime") if verify_resp.get("ok") else "",
                }
            )
        except Exception as exc:
            report["datetime"]["error"] = str(exc)

    before_count = data_count(conn, "user")
    report["user_write"]["before_count"] = before_count.get("result")
    dummy = "\t".join([
        "Pin=999901",
        "CardNo=999901",
        "Name=PROVISION_PROBE",
        "Group=1",
        "StartTime=2000-01-01 00:00:00",
        "EndTime=2099-12-31 23:59:59",
    ])
    set_user = set_device_data(conn, table="user", data=dummy, option="")
    after_count = data_count(conn, "user")
    verify_user = query_data(conn, table="user", fields="Pin,CardNo,Group,Name", filter="Pin=999901", option="")
    delete_resp = delete_device_data(conn, table="user", filter="Pin=999901")
    report["user_write"].update(
        {
            "supported": int(set_user.get("result", -1) or -1) >= 0,
            "write_result": set_user.get("result"),
            "after_count": after_count.get("result"),
            "verify_result": verify_user.get("result"),
            "verify_preview": str(verify_user.get("data") or "")[:240],
            "cleanup_result": delete_resp.get("result"),
        }
    )
    return report


def bind_controller(snapshot: dict[str, Any], *, name: str = "", serial_number: str = "", clear_on_add: bool = False, comm_password: str = "") -> dict[str, Any]:
    identify = dict(snapshot.get("identify") or {})
    options = dict(snapshot.get("options") or {})
    ip = str(identify.get("ip") or snapshot.get("target", {}).get("ip") or "").strip()
    if not ip:
        raise ValueError("missing-ip")
    serial = str(serial_number or identify.get("serial_number") or "").strip()
    if not serial:
        serial = str(name or identify.get("device_name") or ip)
    device_name = str(name or identify.get("device_name") or identify.get("product") or f"Centrala {ip}").strip()
    hardware_version = str(identify.get("product") or options.get("Product") or "").strip()
    firmware_version = str(options.get("FirmVer") or "").strip()
    gateway = str(identify.get("gateway") or options.get("GATEIPAddress") or "").strip()
    netmask = str(identify.get("netmask") or options.get("NetMask") or "").strip()
    route_resolution = resolve_port_route(
        snapshot.get("target", {}).get("configured_port") or snapshot.get("target", {}).get("port") or 4370,
        option_pairs=options,
        device_name=device_name,
        hardware_version=hardware_version,
        firmware_version=firmware_version,
    )
    port = int(route_resolution.get("effective_port") or snapshot.get("target", {}).get("port") or 4370)

    defaults = {
        "name": device_name,
        "serial_number": serial,
        "port": port,
        "device_type": "access_panel",
        "comm_mode": "tcp",
        "enabled": True,
        "hardware_version": hardware_version,
        "firmware_version": firmware_version,
        "gateway": gateway or None,
        "subnet_mask": netmask,
        "comm_password": str(comm_password or ""),
        "clear_on_add": bool(clear_on_add),
    }
    try:
        dev, created = Device.objects.get_or_create(ip_address=ip, defaults=defaults)
    except IntegrityError:
        dev = Device.objects.filter(serial_number=serial).first() or Device.objects.get(ip_address=ip)
        created = False

    update_fields = ["name", "serial_number", "port", "device_type", "comm_mode", "enabled", "hardware_version", "firmware_version", "subnet_mask", "clear_on_add"]
    dev.name = device_name
    dev.serial_number = serial
    dev.port = port
    dev.device_type = "access_panel"
    dev.comm_mode = "tcp"
    dev.enabled = True
    dev.hardware_version = hardware_version
    dev.firmware_version = firmware_version
    dev.subnet_mask = netmask
    dev.clear_on_add = bool(clear_on_add)
    if gateway:
        dev.gateway = gateway
        update_fields.append("gateway")
    if str(comm_password or "").strip() or not str(dev.comm_password or "").strip():
        dev.comm_password = str(comm_password or "")
        update_fields.append("comm_password")
    dev.save(update_fields=sorted(set(update_fields)))

    status, _ = DeviceStatus.objects.get_or_create(device=dev)
    status.online = bool(snapshot.get("options_ok"))
    status.save(update_fields=["online", "updated_at"])

    provision = ensure_controller_doors(dev)
    return {
        "device_id": int(dev.id),
        "created": bool(created),
        "effective_port": int(port),
        "route_resolution": route_resolution,
        "door_capacity": int(getattr(provision, "capacity", 0) or 0),
        "doors_created": int(getattr(provision, "created", 0) or 0),
        "doors_existing": int(getattr(provision, "existing", 0) or 0),
    }