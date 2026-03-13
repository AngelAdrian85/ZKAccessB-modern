from __future__ import annotations

import base64
import hashlib
import json
import re
from typing import Any

import requests
import urllib3
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from agent.models import Device


_VAR_RE = re.compile(r'var\s+([A-Za-z0-9_]+)\s*=\s*"([^"]*)";')
_SUCCESS_MARKER = "[Success] Login Success!"
_DEFAULT_COMMANDS = (
    "getdeviceinfo",
    "getnetattr",
    "getpushserverattr",
    "getdevlevel",
    "getcommpwd",
)


def _parse_var_payload(text: str) -> dict[str, str]:
    return {key: value for key, value in _VAR_RE.findall(str(text or ""))}


def _resolve_device(*, device_id: int, sn: str, ip: str):
    dev = None
    if device_id > 0:
        dev = Device.objects.filter(pk=device_id).first()
    if dev is None and sn:
        dev = Device.objects.filter(serial_number=sn).first()
    if dev is None and ip:
        dev = Device.objects.filter(ip_address=ip).first()
    return dev


class Command(BaseCommand):
    help = "Authenticate to a controller web UI and read firmware CGI parameters such as TCPPort, HTTPPort, push target, and ComPwd."

    def add_arguments(self, parser):
        parser.add_argument("--device-id", type=int, default=0, help="Device.id")
        parser.add_argument("--sn", type=str, default="", help="Device serial number")
        parser.add_argument("--ip", type=str, default="", help="Controller IP override")
        parser.add_argument("--username", type=str, required=True, help="Controller web UI username")
        parser.add_argument("--password", type=str, required=True, help="Controller web UI password")
        parser.add_argument("--timeout-sec", type=float, default=10.0, help="HTTPS request timeout in seconds")
        parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    def handle(self, *args, **options):
        device_id = int(options.get("device_id") or 0)
        sn = str(options.get("sn") or "").strip()
        ip_override = str(options.get("ip") or "").strip()
        username = str(options.get("username") or "").strip()
        password = str(options.get("password") or "")
        timeout_sec = max(2.0, float(options.get("timeout_sec") or 10.0))
        fmt = str(options.get("format") or "text").strip().lower()

        dev = _resolve_device(device_id=device_id, sn=sn, ip=ip_override)
        ip = ip_override or str(getattr(dev, "ip_address", "") or "").strip()
        if not ip:
            raise CommandError("Controller IP not resolved. Pass --ip or identify a saved device with --device-id/--sn.")

        session = requests.Session()
        session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": f"https://{ip}",
                "Referer": f"https://{ip}/login.html",
                "Accept": "*/*",
            }
        )

        bootstrap = []
        for path in ("/", "/index.html", "/login.html"):
            url = f"https://{ip}{path}"
            resp = session.get(url, timeout=timeout_sec)
            bootstrap.append({"path": path, "status": resp.status_code})

        username_b64 = base64.b64encode(username.encode("utf-8")).decode("ascii")
        password_md5 = hashlib.md5(password.encode("utf-8")).hexdigest()
        login_resp = session.post(
            f"https://{ip}/cgi-bin/login.cgi",
            data={"-username": username_b64, "-userpass": password_md5},
            timeout=timeout_sec,
        )
        login_text = str(login_resp.text or "")
        login_ok = _SUCCESS_MARKER in login_text
        if not login_ok:
            raise CommandError(f"Controller login failed: HTTP {login_resp.status_code} body={login_text[:200]!r}")

        command_payloads: dict[str, dict[str, Any]] = {}
        for cmd in _DEFAULT_COMMANDS:
            resp = session.post(
                f"https://{ip}/cgi-bin/param.cgi",
                data={"cmd": cmd},
                timeout=timeout_sec,
            )
            text = str(resp.text or "")
            command_payloads[cmd] = {
                "status_code": resp.status_code,
                "raw": text,
                "values": _parse_var_payload(text),
            }

        info = command_payloads.get("getdeviceinfo", {}).get("values", {})
        net = command_payloads.get("getnetattr", {}).get("values", {})
        push = command_payloads.get("getpushserverattr", {}).get("values", {})
        devlevel = command_payloads.get("getdevlevel", {}).get("values", {})
        commpwd = command_payloads.get("getcommpwd", {}).get("values", {})
        expected_comm_pwd = str(getattr(dev, "comm_password", "") or "").strip() if dev is not None else ""
        if not expected_comm_pwd:
            try:
                expected_comm_pwd = str(getattr(settings, "ZKACCESS_DEFAULT_COMM_PASSWORD", "") or "").strip()
            except Exception:
                expected_comm_pwd = ""

        report = {
            "ok": True,
            "device_id": getattr(dev, "id", None),
            "serial_number": str(getattr(dev, "serial_number", "") or info.get("SerialNumber") or ""),
            "ip_address": ip,
            "bootstrap": bootstrap,
            "session_cookies": sorted(session.cookies.get_dict().keys()),
            "firmware": {
                "device_name": info.get("DeviceName") or "",
                "platform": info.get("Platform") or "",
                "firmware_version": info.get("FirmVer") or "",
                "tcp_port": info.get("TCPPort") or net.get("TCPPort") or "",
                "http_port": info.get("HTTPPort") or net.get("HTTPPort") or "",
                "ip_address": info.get("IPAddress") or net.get("IPAddress") or ip,
                "netmask": info.get("NetMask") or net.get("NetMask") or "",
                "gateway": info.get("GATEIPAddress") or net.get("GATEIPAddress") or "",
                "push_server_ip": push.get("WebServerIP") or "",
                "push_server_port": push.get("WebServerPort") or "",
                "push_server_url": push.get("WebServerURL") or "",
                "push_fun_on": devlevel.get("PushFunOn") or "",
                "comm_password": commpwd.get("ComPwd") or "",
                "comm_password_matches_expected": bool(expected_comm_pwd) and (commpwd.get("ComPwd") == expected_comm_pwd),
            },
            "commands": command_payloads,
            "summary": {
                "push_lane_configured": (push.get("WebServerIP") or "") != "" and str(devlevel.get("PushFunOn") or "") == "1",
                "server_to_controller_lane": f"{ip}:{info.get('TCPPort') or net.get('TCPPort') or ''}",
                "controller_to_server_lane": f"{push.get('WebServerIP') or ''}:{push.get('WebServerPort') or ''}",
            },
        }

        if fmt == "json":
            self.stdout.write(json.dumps(report, indent=2, ensure_ascii=True))
            return

        fw = report["firmware"]
        self.stdout.write(f"Controller web login OK for {ip}")
        self.stdout.write(
            f"Device={fw['device_name'] or '-'} Platform={fw['platform'] or '-'} Firmware={fw['firmware_version'] or '-'}"
        )
        self.stdout.write(f"Firmware network: IP={fw['ip_address'] or '-'} TCPPort={fw['tcp_port'] or '-'} HTTPPort={fw['http_port'] or '-'}")
        self.stdout.write(
            f"Push lane: WebServerIP={fw['push_server_ip'] or '-'} WebServerPort={fw['push_server_port'] or '-'} PushFunOn={fw['push_fun_on'] or '-'}"
        )
        self.stdout.write(f"Push URL: {fw['push_server_url'] or '-'}")
        self.stdout.write(f"Comm password in firmware: {'matches expected' if fw['comm_password_matches_expected'] else 'differs/unknown'}")
        self.stdout.write(
            f"Lane summary: server->controller={report['summary']['server_to_controller_lane']} ; controller->server={report['summary']['controller_to_server_lane']}"
        )