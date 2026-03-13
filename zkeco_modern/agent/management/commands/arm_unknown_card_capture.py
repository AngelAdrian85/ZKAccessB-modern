from __future__ import annotations

import configparser
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from agent.diagnostic_ports import get_default_comm_password
from agent.models import Device, Door, WiegandCardFormat


REPO_ROOT = Path(__file__).resolve().parents[4]
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def detect_local_server_url(explicit_url: str = "") -> str:
    value = str(explicit_url or "").strip()
    if value:
        return value.rstrip("/")
    port = 15437
    ini_path = Path.home() / "zkeco_tray_config.ini"
    try:
        if ini_path.exists():
            parser = configparser.ConfigParser(strict=False)
            parser.read(ini_path, encoding="utf-8-sig")
            if parser.has_section("tray") and parser.has_option("tray", "port"):
                port = int(str(parser.get("tray", "port") or "15437").strip() or "15437")
    except Exception:
        port = 15437
    return f"http://127.0.0.1:{port}"


def _heartbeat_path(strategy: str) -> Path:
    if str(strategy or "").strip().lower() == "w26":
        return Path.home() / "zkeco_reader_heartbeat_wiegand.json"
    return Path.home() / "zkeco_reader_heartbeat_zkemkeeper.json"


def _pid_file_path(strategy: str) -> Path:
    suffix = "w26" if str(strategy or "").strip().lower() == "w26" else "zkemkeeper"
    return REPO_ROOT / f"tmp_unknown_card_capture_{suffix}.json"


def _load_pid_info(strategy: str) -> dict[str, Any]:
    path = _pid_file_path(strategy)
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8-sig")) or {}
    except Exception:
        pass
    return {}


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8-sig")) or {}
    except Exception:
        pass
    return {}


def _pid_running(pid: int) -> bool:
    try:
        proc = subprocess.run(
            ["tasklist", "/FI", f"PID eq {int(pid)}"],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return False
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    return str(int(pid)) in output and "No tasks are running" not in output


def _kill_pid(pid: int) -> bool:
    try:
        proc = subprocess.run(
            ["taskkill", "/PID", str(int(pid)), "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
        return int(proc.returncode or 0) == 0
    except Exception:
        return False


def _resolve_device(*, device_id: int = 0, ip: str = "") -> Device:
    if int(device_id or 0) > 0:
        dev = Device.objects.filter(pk=int(device_id)).first()
        if dev is not None:
            return dev
    ip_text = str(ip or "").strip()
    if ip_text:
        dev = Device.objects.filter(ip_address=ip_text).first()
        if dev is not None:
            return dev
    raise CommandError("Device not found. Use --device-id or --ip.")


def _resolve_door(device: Device, *, door_pk: int = 0, door_id: str = "") -> Door | None:
    if int(door_pk or 0) > 0:
        return Door.objects.select_related("device").filter(pk=int(door_pk), device_id=int(device.id)).first()
    door_id_text = str(door_id or "").strip()
    if door_id_text.isdigit():
        return (
            Door.objects.select_related("device")
            .filter(device_id=int(device.id), door_number=int(door_id_text))
            .first()
        )
    return (
        Door.objects.select_related("device")
        .filter(device_id=int(device.id))
        .exclude(door_number__isnull=True)
        .exclude(door_number=0)
        .order_by("door_number", "id")
        .first()
    )


def _default_wiegand_format_name() -> str:
    try:
        active = WiegandCardFormat.objects.filter(is_active=True).order_by("-system_defined", "wiegand_name").first()
        if active is not None:
            return str(active.wiegand_name or "").strip() or "Wiegand 26"
    except Exception:
        pass
    return "Wiegand 26"


def detect_zkemkeeper_sdk_dir(explicit_dir: str = "") -> str:
    value = str(explicit_dir or "").strip()
    if value and Path(value).exists():
        return value
    resurse_root = REPO_ROOT / "Resurse"
    try:
        candidates = sorted(resurse_root.rglob("zkemkeeper.dll"), key=lambda path: str(path).lower())
    except Exception:
        candidates = []
    for candidate in candidates:
        normalized = str(candidate).replace("/", "\\").lower()
        if normalized.endswith("\\x64\\zkemkeeper.dll") or normalized.endswith("\\64bits\\zkemkeeper.dll"):
            return str(candidate.parent)
    return ""


def build_capture_config(
    *,
    device: Device,
    strategy: str = "auto",
    server_url: str = "",
    port: int = 0,
    comm_password: str = "",
    door_pk: int = 0,
    door_id: str = "",
    machine_number: int = 1,
    engine: str = "",
    listen_host: str = "0.0.0.0",
    listen_port: int = 9001,
    format_name: str = "",
    source: str = "",
    auto_register: bool = True,
) -> dict[str, Any]:
    selected_strategy = str(strategy or "auto").strip().lower() or "auto"
    if selected_strategy == "auto":
        selected_strategy = "zkemkeeper"

    selected_engine = str(engine or os.environ.get("ZKACCESS_ZKEMKEEPER_ENGINE") or "vbs").strip().lower() or "vbs"
    if selected_engine not in {"vbs", "ps1"}:
        selected_engine = "vbs"

    resolved_server_url = detect_local_server_url(server_url)
    target_port = int(port or getattr(device, "port", 0) or 14370)
    password = str(comm_password or getattr(device, "comm_password", "") or get_default_comm_password() or "").strip()
    door_obj = _resolve_door(device, door_pk=int(door_pk or 0), door_id=door_id)
    resolved_door_pk = int(getattr(door_obj, "id", 0) or 0)
    resolved_door_number = str(getattr(door_obj, "door_number", "") or "")
    dump_suffix = int(getattr(device, "id", 0) or 0) or "unknown"

    if selected_strategy == "w26":
        effective_format_name = str(format_name or _default_wiegand_format_name()).strip() or "Wiegand 26"
        resolved_source = str(source or f"w26-device-{int(device.id)}").strip()
        command = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "wiegand_listener.py"),
            "--server-url",
            resolved_server_url,
            "--listen-host",
            str(listen_host or "0.0.0.0"),
            "--listen-port",
            str(int(listen_port or 9001)),
            "--format-name",
            effective_format_name,
            "--device-id",
            str(int(device.id)),
            "--source",
            resolved_source,
        ]
        if resolved_door_number:
            command.extend(["--door-id", resolved_door_number])
        if resolved_door_pk:
            command.extend(["--door-pk", str(resolved_door_pk)])
        return {
            "strategy": "w26",
            "device_id": int(device.id),
            "device_name": str(getattr(device, "name", "") or ""),
            "ip": str(getattr(device, "ip_address", "") or ""),
            "port": int(target_port),
            "door_pk": resolved_door_pk,
            "door_number": resolved_door_number,
            "door_name": str(getattr(door_obj, "name", "") or ""),
            "server_url": resolved_server_url,
            "format_name": effective_format_name,
            "listen_host": str(listen_host or "0.0.0.0"),
            "listen_port": int(listen_port or 9001),
            "source": resolved_source,
            "command": command,
            "stdout_log": str(REPO_ROOT / f"unknown_card_capture_w26_{dump_suffix}.out.log"),
            "stderr_log": str(REPO_ROOT / f"unknown_card_capture_w26_{dump_suffix}.err.log"),
            "heartbeat_path": str(_heartbeat_path("w26")),
            "pid_file": str(_pid_file_path("w26")),
        }

    resolved_source = str(source or f"zkemkeeper-c{int(device.id)}").strip()
    script_path = REPO_ROOT / "scripts" / ("zkemkeeper_event_bridge.vbs" if selected_engine == "vbs" else "zkemkeeper_event_bridge.ps1")
    dump_file = REPO_ROOT / f"zkemkeeper_event_dump_controller{dump_suffix}.jsonl"
    sdk_dir = detect_zkemkeeper_sdk_dir(os.environ.get("ZKACCESS_ZKEMKEEPER_SDK_DIR", ""))
    if selected_engine == "vbs":
        command = [
            "cscript.exe",
            "//nologo",
            str(script_path),
            f"/Ip:{str(getattr(device, 'ip_address', '') or '')}",
            f"/Port:{int(target_port)}",
            f"/MachineNumber:{int(machine_number or 1)}",
            f"/ServerUrl:{resolved_server_url}",
            f"/DeviceId:{int(device.id)}",
            f"/Source:{resolved_source}",
            f"/DumpFile:{str(dump_file)}",
        ]
        if sdk_dir:
            command.append(f"/SdkDir:{sdk_dir}")
        if resolved_door_number:
            command.append(f"/DoorId:{resolved_door_number}")
        if resolved_door_pk:
            command.append(f"/DoorPk:{resolved_door_pk}")
        if password:
            command.append(f"/CommPassword:{password}")
        if auto_register:
            command.append("/AutoRegister:1")
    else:
        command = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            "-Ip",
            str(getattr(device, "ip_address", "") or ""),
            "-Port",
            str(int(target_port)),
            "-MachineNumber",
            str(int(machine_number or 1)),
            "-ServerUrl",
            resolved_server_url,
            "-DeviceId",
            str(int(device.id)),
            "-Source",
            resolved_source,
            "-DumpFile",
            str(dump_file),
        ]
        if sdk_dir:
            command.extend(["-SdkDir", sdk_dir])
        if resolved_door_number:
            command.extend(["-DoorId", resolved_door_number])
        if resolved_door_pk:
            command.extend(["-DoorPk", str(resolved_door_pk)])
        if password:
            command.extend(["-CommPassword", password])
        if auto_register:
            command.append("-AutoRegister")
    return {
        "strategy": "zkemkeeper",
        "engine": selected_engine,
        "device_id": int(device.id),
        "device_name": str(getattr(device, "name", "") or ""),
        "ip": str(getattr(device, "ip_address", "") or ""),
        "port": int(target_port),
        "door_pk": resolved_door_pk,
        "door_number": resolved_door_number,
        "door_name": str(getattr(door_obj, "name", "") or ""),
        "server_url": resolved_server_url,
        "comm_password_present": bool(password),
        "machine_number": int(machine_number or 1),
        "source": resolved_source,
        "sdk_dir": sdk_dir,
        "dump_file": str(dump_file),
        "command": command,
        "stdout_log": str(REPO_ROOT / f"unknown_card_capture_zkem_{dump_suffix}.out.log"),
        "stderr_log": str(REPO_ROOT / f"unknown_card_capture_zkem_{dump_suffix}.err.log"),
        "heartbeat_path": str(_heartbeat_path("zkemkeeper")),
        "pid_file": str(_pid_file_path("zkemkeeper")),
    }


def _launch_capture(config: dict[str, Any]) -> dict[str, Any]:
    command = list(config.get("command") or [])
    if not command:
        raise CommandError("Missing launch command")
    script_target = Path(str(command[1] if len(command) > 1 else command[0]))
    if command[0] == sys.executable and len(command) > 1:
        script_target = Path(str(command[1]))
    if command[0].lower().endswith("cscript.exe") and len(command) > 2:
        script_target = Path(str(command[2]))
    if command[0].lower() == "powershell" and len(command) > 4:
        script_target = Path(str(command[4]))
    if script_target.suffix and not script_target.exists():
        raise CommandError(f"Missing script: {script_target}")

    stop_capture(str(config.get("strategy") or ""))
    stdout_path = Path(str(config.get("stdout_log") or "")).resolve()
    stderr_path = Path(str(config.get("stderr_log") or "")).resolve()
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("ab") as stdout_handle, stderr_path.open("ab") as stderr_handle:
        proc = subprocess.Popen(
            command,
            cwd=str(REPO_ROOT),
            stdout=stdout_handle,
            stderr=stderr_handle,
            creationflags=CREATE_NO_WINDOW,
        )
    pid_payload = {
        "strategy": str(config.get("strategy") or ""),
        "pid": int(proc.pid),
        "started_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "heartbeat_path": str(config.get("heartbeat_path") or ""),
        "dump_file": str(config.get("dump_file") or ""),
        "device_id": int(config.get("device_id") or 0),
        "command": command,
    }
    _pid_file_path(str(config.get("strategy") or "")).write_text(
        json.dumps(pid_payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    return pid_payload


def stop_capture(strategy: str) -> dict[str, Any]:
    selected = "w26" if str(strategy or "").strip().lower() == "w26" else "zkemkeeper"
    pid_info = _load_pid_info(selected)
    pid = int(pid_info.get("pid") or 0)
    stopped = False
    if pid > 0:
        stopped = _kill_pid(pid)
    pid_path = _pid_file_path(selected)
    try:
        if pid_path.exists():
            pid_path.unlink()
    except Exception:
        pass
    return {
        "strategy": selected,
        "pid": pid,
        "stopped": bool(stopped),
    }


def capture_status(config: dict[str, Any]) -> dict[str, Any]:
    strategy = str(config.get("strategy") or "zkemkeeper")
    heartbeat = _read_json_file(Path(str(config.get("heartbeat_path") or _heartbeat_path(strategy))))
    pid_info = _load_pid_info(strategy)
    pid = int(pid_info.get("pid") or 0)
    dump_text = str(config.get("dump_file") or "").strip()
    dump_path = Path(dump_text) if dump_text else None
    return {
        **config,
        "heartbeat": heartbeat,
        "pid": pid,
        "running": bool(pid and _pid_running(pid)),
        "pid_info": pid_info,
        "dump_exists": bool(dump_path is not None and dump_path.exists()),
        "dump_size": int(dump_path.stat().st_size) if dump_path is not None and dump_path.exists() else 0,
    }


class Command(BaseCommand):
    help = "Arm, inspect, or stop the recommended unknown-card capture path for a controller."

    def add_arguments(self, parser):
        parser.add_argument("--device-id", type=int, default=22, help="Device.id to arm")
        parser.add_argument("--ip", type=str, default="", help="Resolve device by IP when device id is not known")
        parser.add_argument("--strategy", choices=["auto", "zkemkeeper", "w26"], default="auto", help="Capture strategy")
        parser.add_argument("--launch", action="store_true", help="Launch capture in background")
        parser.add_argument("--stop", action="store_true", help="Stop the recorded capture PID for this strategy")
        parser.add_argument("--status", action="store_true", help="Show capture status (default action)")
        parser.add_argument("--server-url", type=str, default="", help="Base local server URL; auto-detected from zkeco_tray_config.ini when omitted")
        parser.add_argument("--port", type=int, default=0, help="Override controller port")
        parser.add_argument("--comm-password", type=str, default="", help="Override controller comm password")
        parser.add_argument("--door-pk", type=int, default=0, help="Bind capture to a specific Door.pk")
        parser.add_argument("--door-id", type=str, default="", help="Bind capture to a specific controller door number")
        parser.add_argument("--machine-number", type=int, default=1, help="ZKEMKeeper machine number")
        parser.add_argument("--engine", choices=["vbs", "ps1"], default="", help="ZKEMKeeper bridge engine")
        parser.add_argument("--listen-host", type=str, default="0.0.0.0", help="Host for W26 listener")
        parser.add_argument("--listen-port", type=int, default=9001, help="Port for W26 listener")
        parser.add_argument("--format-name", type=str, default="", help="Wiegand format name for the W26 listener")
        parser.add_argument("--source", type=str, default="", help="Source label stored in the monitor stream")
        parser.add_argument("--no-autoreg", action="store_true", help="Disable automatic COM registration for zkemkeeper bridge launch")
        parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    def handle(self, *args, **options):
        selected_strategy = str(options.get("strategy") or "auto")
        if not any(bool(options.get(key)) for key in ("launch", "stop", "status")):
            options["status"] = True

        if bool(options.get("stop")):
            stop_result = stop_capture(selected_strategy)
            if str(options.get("format") or "text") == "json":
                self.stdout.write(json.dumps(stop_result, indent=2, ensure_ascii=True))
            else:
                self.stdout.write(f"Stopped strategy={stop_result['strategy']} pid={stop_result['pid'] or '-'} ok={stop_result['stopped']}")
            if not bool(options.get("status")):
                return

        device = _resolve_device(device_id=int(options.get("device_id") or 0), ip=str(options.get("ip") or ""))
        config = build_capture_config(
            device=device,
            strategy=selected_strategy,
            server_url=str(options.get("server_url") or ""),
            port=int(options.get("port") or 0),
            comm_password=str(options.get("comm_password") or ""),
            door_pk=int(options.get("door_pk") or 0),
            door_id=str(options.get("door_id") or ""),
            machine_number=int(options.get("machine_number") or 1),
            engine=str(options.get("engine") or ""),
            listen_host=str(options.get("listen_host") or "0.0.0.0"),
            listen_port=int(options.get("listen_port") or 9001),
            format_name=str(options.get("format_name") or ""),
            source=str(options.get("source") or ""),
            auto_register=not bool(options.get("no_autoreg")),
        )

        launch_info = None
        if bool(options.get("launch")):
            launch_info = _launch_capture(config)

        report = capture_status(config)
        if launch_info is not None:
            report["launch"] = launch_info

        out_format = str(options.get("format") or "text")
        if out_format == "json":
            self.stdout.write(json.dumps(report, indent=2, ensure_ascii=True))
            return

        self.stdout.write(
            f"Capture strategy={report['strategy']} running={'YES' if report['running'] else 'NO'} pid={report['pid'] or '-'}"
        )
        self.stdout.write(
            f"Device: id={report['device_id']} name={report['device_name']} ip={report['ip']} port={report['port']}"
        )
        if report.get("door_number"):
            self.stdout.write(
                f"Door: number={report['door_number']} pk={report['door_pk'] or '-'} name={report.get('door_name') or ''}"
            )
        self.stdout.write(f"Server URL: {report['server_url']}")
        if report.get("strategy") == "zkemkeeper":
            self.stdout.write(
                f"Bridge: engine={report.get('engine')} machine={report.get('machine_number')} comm_password_present={report.get('comm_password_present')}"
            )
        if report.get("strategy") == "w26":
            self.stdout.write(
                f"Listener: {report.get('listen_host')}:{report.get('listen_port')} format={report.get('format_name')}"
            )
        self.stdout.write(f"Heartbeat: {report.get('heartbeat_path')}")
        self.stdout.write(f"Dump: {report.get('dump_file') or '-'} size={report.get('dump_size')} exists={report.get('dump_exists')}")
        hb = report.get("heartbeat") or {}
        if hb:
            self.stdout.write(
                f"Heartbeat status={hb.get('status') or '-'} last_event={hb.get('last_event') or '-'} last_card={hb.get('last_card') or '-'}"
            )
        self.stdout.write("Command:")
        self.stdout.write("  " + " ".join(str(part) for part in (report.get("command") or [])))
