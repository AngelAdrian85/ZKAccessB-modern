from __future__ import annotations

from typing import Any

from django.conf import settings


def _normalize_port(value: Any) -> int | None:
    try:
        port = int(value)
    except Exception:
        return None
    if port <= 0 or port > 65535:
        return None
    return port


def _unique_ports(values: list[Any]) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for value in values:
        port = _normalize_port(value)
        if port is None or port in seen:
            continue
        seen.add(port)
        out.append(port)
    return out


def get_default_comm_password() -> str:
    try:
        from agent.models import SystemSettings

        ss = SystemSettings.get_solo()
        pw_db = str(getattr(ss, "default_comm_password", "") or "").strip()
        if pw_db:
            return pw_db
    except Exception:
        pass
    try:
        return str(getattr(settings, "ZKACCESS_DEFAULT_COMM_PASSWORD", "") or "").strip()
    except Exception:
        return ""


def lookup_device(*, device_id: int = 0, ip: str = ""):
    try:
        from agent.models import Device

        if int(device_id or 0) > 0:
            return Device.objects.filter(pk=int(device_id)).first()
        ip_txt = str(ip or "").strip()
        if ip_txt:
            return Device.objects.filter(ip_address=ip_txt).first()
    except Exception:
        return None
    return None


def password_candidates(*, supplied_password: str = "", device=None) -> list[str]:
    values: list[str] = []
    supplied = str(supplied_password or "")
    if supplied:
        values.append(supplied)
    try:
        dev_pw = str(getattr(device, "comm_password", "") or "").strip()
        if dev_pw:
            values.append(dev_pw)
    except Exception:
        pass
    default_pw = get_default_comm_password()
    if default_pw:
        values.append(default_pw)
    values.extend(["", "0"])

    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def resolve_diagnostic_route(
    *,
    device=None,
    configured_port: int | None = None,
    strict_port: bool = False,
    extra_ports: tuple[int, ...] | list[int] = (),
) -> dict[str, Any]:
    from agent.controller_capabilities import resolve_port_route

    route = resolve_port_route(
        configured_port if configured_port is not None else getattr(device, "port", None),
        device_name=str(getattr(device, "name", "") or ""),
        hardware_version=str(getattr(device, "hardware_version", "") or ""),
        firmware_version=str(getattr(device, "firmware_version", "") or ""),
    )
    if strict_port and configured_port is not None:
        candidate_ports = [int(configured_port)]
    else:
        candidate_ports = _unique_ports(
            list(route.get("candidate_ports") or [])
            + [configured_port]
            + list(extra_ports or [])
            + [14370, 4370, 4371, 4372]
        )
    return {
        "route": route,
        "candidate_ports": candidate_ports,
        "effective_port": int(route.get("effective_port") or configured_port or 4370),
    }