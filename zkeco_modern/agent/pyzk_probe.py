from __future__ import annotations

import argparse
import json
import time
import traceback
from dataclasses import dataclass
from typing import Any

from zk import ZK


@dataclass
class AttemptConfig:
    transport: str
    ip: str
    port: int
    password: str
    timeout: int
    verbose: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Probe a live ZKTeco controller with pyzk. Note: the correct package is 'pyzk', "
            "even though the import name is 'zk'."
        )
    )
    parser.add_argument("--device-id", type=int, default=0, help="Load IP/port/password from Django Device")
    parser.add_argument("--ip", default="", help="Controller IP")
    parser.add_argument("--port", type=int, default=0, help="Primary port to test")
    parser.add_argument(
        "--ports",
        default="",
        help="Comma-separated extra ports to test, e.g. 14370,4370",
    )
    parser.add_argument(
        "--password",
        action="append",
        default=[],
        help="Password candidate; repeat flag for multiple values",
    )
    parser.add_argument("--timeout", type=int, default=8, help="Per-attempt timeout in seconds")
    parser.add_argument(
        "--transport",
        choices=["tcp", "udp", "both"],
        default="both",
        help="Which transport variants pyzk should try",
    )
    parser.add_argument("--live-seconds", type=int, default=0, help="Capture live events for N seconds after connect")
    parser.add_argument("--skip-users", action="store_true", help="Skip get_users()")
    parser.add_argument("--skip-attendance", action="store_true", help="Skip get_attendance()")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    parser.add_argument("--verbose", action="store_true", help="Enable pyzk verbose mode")
    return parser


def _dedupe_keep_order(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def load_device_defaults(device_id: int) -> dict[str, Any]:
    if int(device_id or 0) <= 0:
        return {}
    from agent.models import Device

    device = Device.objects.get(pk=int(device_id))
    return {
        "device_id": int(device.id),
        "ip": str(device.ip_address or "").strip(),
        "port": int(device.port or 0),
        "password": str(device.comm_password or "").strip(),
        "name": str(device.name or "").strip(),
        "serial_number": str(device.serial_number or "").strip(),
    }


def resolve_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], list[int], list[str]]:
    device_defaults = load_device_defaults(int(args.device_id or 0))
    ip = str(args.ip or device_defaults.get("ip") or "").strip()
    if not ip:
        raise SystemExit("Missing --ip or --device-id")

    ports: list[int] = []
    primary_port = int(args.port or device_defaults.get("port") or 0)
    if primary_port > 0:
        ports.append(primary_port)
    if str(args.ports or "").strip():
        for raw in str(args.ports).split(","):
            raw = raw.strip()
            if not raw:
                continue
            ports.append(int(raw))
    ports.extend([14370, 4370])

    passwords = list(args.password or [])
    if str(device_defaults.get("password") or "").strip():
        passwords.append(str(device_defaults["password"]))
    passwords.extend(["0", "2468", ""])

    ports_out: list[int] = []
    seen_ports: set[int] = set()
    for port in ports:
        if int(port) <= 0 or int(port) in seen_ports:
            continue
        seen_ports.add(int(port))
        ports_out.append(int(port))

    return device_defaults, ports_out, _dedupe_keep_order(passwords)


def _password_to_int(password: str) -> int:
    text = str(password or "0").strip()
    if text == "":
        return 0
    return int(text)


def _user_to_dict(user: Any) -> dict[str, Any]:
    return {
        "uid": getattr(user, "uid", None),
        "user_id": getattr(user, "user_id", None),
        "name": getattr(user, "name", None),
        "card": getattr(user, "card", None),
        "group_id": getattr(user, "group_id", None),
        "privilege": getattr(user, "privilege", None),
    }


def _attendance_to_dict(attendance: Any) -> dict[str, Any]:
    timestamp = getattr(attendance, "timestamp", None)
    if hasattr(timestamp, "isoformat"):
        timestamp = timestamp.isoformat()
    return {
        "uid": getattr(attendance, "uid", None),
        "user_id": getattr(attendance, "user_id", None),
        "status": getattr(attendance, "status", None),
        "punch": getattr(attendance, "punch", None),
        "timestamp": timestamp,
    }


def _capture_live_events(conn: Any, seconds: int) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if int(seconds or 0) <= 0:
        return events
    deadline = time.time() + int(seconds)
    stream = conn.live_capture(new_timeout=min(max(2, int(seconds)), 10))
    try:
        while time.time() < deadline:
            event = next(stream)
            if event is None:
                continue
            events.append(_attendance_to_dict(event))
    finally:
        setattr(conn, "end_live_capture", True)
        try:
            next(stream)
        except StopIteration:
            pass
        except Exception:
            pass
    return events


def run_attempt(cfg: AttemptConfig, *, read_users: bool, read_attendance: bool, live_seconds: int) -> dict[str, Any]:
    started = time.time()
    result: dict[str, Any] = {
        "transport": cfg.transport,
        "ip": cfg.ip,
        "port": int(cfg.port),
        "password": cfg.password,
        "timeout": int(cfg.timeout),
        "connected": False,
        "elapsed_seconds": 0.0,
    }
    conn = None
    try:
        zk = ZK(
            cfg.ip,
            port=int(cfg.port),
            timeout=int(cfg.timeout),
            password=_password_to_int(cfg.password),
            force_udp=(cfg.transport == "udp"),
            verbose=bool(cfg.verbose),
        )
        conn = zk.connect()
        result["connected"] = True

        size_ok = conn.read_sizes()
        result["sizes"] = {
            "ok": bool(size_ok),
            "users": getattr(conn, "users", None),
            "records": getattr(conn, "records", None),
            "cards": getattr(conn, "cards", None),
            "users_cap": getattr(conn, "users_cap", None),
            "rec_cap": getattr(conn, "rec_cap", None),
        }

        if read_users:
            users = conn.get_users()
            result["users"] = {
                "count": len(users),
                "sample": [_user_to_dict(user) for user in users[:5]],
            }

        if read_attendance:
            attendance = conn.get_attendance()
            result["attendance"] = {
                "count": len(attendance),
                "sample": [_attendance_to_dict(item) for item in attendance[:5]],
            }

        if int(live_seconds or 0) > 0:
            result["live_capture"] = {
                "seconds": int(live_seconds),
                "events": _capture_live_events(conn, int(live_seconds)),
            }

    except Exception as exc:
        result["error_type"] = exc.__class__.__name__
        result["error"] = str(exc)
        result["traceback"] = traceback.format_exc()
    finally:
        if conn is not None:
            try:
                conn.disconnect()
            except Exception:
                pass
        result["elapsed_seconds"] = round(time.time() - started, 3)
    return result


def attempt_matrix(args: argparse.Namespace, device_defaults: dict[str, Any], ports: list[int], passwords: list[str]) -> dict[str, Any]:
    transports = ["tcp", "udp"] if args.transport == "both" else [args.transport]
    attempts: list[dict[str, Any]] = []
    for port in ports:
        for transport in transports:
            if transport == "udp" and port not in {4370, 14370}:
                continue
            for password in passwords:
                attempts.append(
                    run_attempt(
                        AttemptConfig(
                            transport=transport,
                            ip=str(args.ip or device_defaults.get("ip") or "").strip(),
                            port=int(port),
                            password=str(password),
                            timeout=int(args.timeout),
                            verbose=bool(args.verbose),
                        ),
                        read_users=not bool(args.skip_users),
                        read_attendance=not bool(args.skip_attendance),
                        live_seconds=int(args.live_seconds or 0),
                    )
                )
                if attempts[-1].get("connected"):
                    return {
                        "device": device_defaults,
                        "ports": ports,
                        "passwords": passwords,
                        "attempts": attempts,
                        "first_success": attempts[-1],
                    }
    return {
        "device": device_defaults,
        "ports": ports,
        "passwords": passwords,
        "attempts": attempts,
        "first_success": None,
    }


def render_human(report: dict[str, Any]) -> str:
    lines: list[str] = []
    device = dict(report.get("device") or {})
    if device:
        lines.append(f"Device defaults: {json.dumps(device, ensure_ascii=True)}")
    lines.append(f"Ports tested: {report.get('ports')}")
    lines.append(f"Passwords tested: {report.get('passwords')}")
    lines.append("")
    for index, attempt in enumerate(report.get("attempts") or [], start=1):
        header = (
            f"[{index}] {attempt.get('transport')} {attempt.get('ip')}:{attempt.get('port')} "
            f"password={attempt.get('password')!r} connected={attempt.get('connected')} "
            f"elapsed={attempt.get('elapsed_seconds')}s"
        )
        lines.append(header)
        if attempt.get("connected"):
            lines.append("  sizes: " + json.dumps(attempt.get("sizes") or {}, ensure_ascii=True))
            if "users" in attempt:
                lines.append("  users: " + json.dumps(attempt.get("users") or {}, ensure_ascii=True))
            if "attendance" in attempt:
                lines.append("  attendance: " + json.dumps(attempt.get("attendance") or {}, ensure_ascii=True))
            if "live_capture" in attempt:
                lines.append("  live_capture: " + json.dumps(attempt.get("live_capture") or {}, ensure_ascii=True))
        else:
            lines.append(f"  error: {attempt.get('error_type')} {attempt.get('error')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    device_defaults, ports, passwords = resolve_inputs(args)
    if not str(args.ip or "").strip():
        args.ip = str(device_defaults.get("ip") or "").strip()
    return attempt_matrix(args, device_defaults, ports, passwords)
