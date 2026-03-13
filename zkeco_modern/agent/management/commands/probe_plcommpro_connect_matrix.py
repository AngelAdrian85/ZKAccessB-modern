from __future__ import annotations

import socket
from typing import Any

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Probe plcommpro SDK connectivity across ports/passwords (connect_only) on real hardware. "
        "Also reports which ports are TCP-open."
    )

    def add_arguments(self, parser):
        parser.add_argument("--device-id", type=int, default=0, help="Optional Device id for route-aware metadata")
        parser.add_argument("--ip", type=str, required=True, help="Device IP (e.g. 192.168.1.235)")
        parser.add_argument(
            "--ports",
            type=str,
            default="14370,4370,4371,4372,5000,5001,6000,8000,8080,9000",
            help="Comma-separated TCP ports to scan (default includes common ZK ports)",
        )
        parser.add_argument(
            "--protocols",
            type=str,
            default="TCP,UDP",
            help="Comma-separated plcommpro protocols to try for connect_only (TCP,UDP). Default TCP,UDP.",
        )
        parser.add_argument(
            "--password",
            type=str,
            default=None,
            help="Optional password to try first. If omitted, uses SystemSettings default if set.",
        )
        parser.add_argument(
            "--timeout-ms",
            type=int,
            default=1500,
            help="SDK timeout in ms passed to plcommpro (default 1500)",
        )
        parser.add_argument(
            "--tcp-timeout",
            type=float,
            default=0.35,
            help="TCP connect timeout in seconds for port scan (default 0.35)",
        )
        parser.add_argument(
            "--process-timeout-s",
            type=int,
            default=8,
            help="Bridge process timeout in seconds for connect_only (default 8)",
        )
        parser.add_argument(
            "--strict-ports",
            action="store_true",
            help="Use exactly the supplied --ports list without route-aware overlay.",
        )

    def _tcp_open(self, ip: str, port: int, timeout_s: float) -> bool:
        sock: socket.socket | None = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(float(timeout_s))
            sock.connect((ip, int(port)))
            return True
        except Exception:
            return False
        finally:
            try:
                if sock:
                    sock.close()
            except Exception:
                pass

    def _compact(self, data: Any, max_len: int = 160) -> str:
        s = str(data or "")
        s = s.replace("\r", " ").replace("\n", " ").strip()
        if len(s) > max_len:
            s = s[:max_len] + "…"
        return s

    def handle(self, *args, **options):
        ip = str(options["ip"] or "").strip()
        ports_raw = str(options.get("ports") or "").strip()
        protocols_raw = str(options.get("protocols") or "").strip()
        timeout_ms = int(options.get("timeout_ms") or 1500)
        tcp_timeout = float(options.get("tcp_timeout") or 0.35)
        process_timeout_s = int(options.get("process_timeout_s") or 8)
        strict_ports = bool(options.get("strict_ports"))

        ports: list[int] = []
        for chunk in ports_raw.split(","):
            chunk = (chunk or "").strip()
            if not chunk:
                continue
            try:
                p = int(chunk)
            except Exception:
                continue
            if 1 <= p <= 65535 and p not in ports:
                ports.append(p)

        protocols: list[str] = []
        for chunk in protocols_raw.split(","):
            proto = (chunk or "").strip().upper()
            if not proto:
                continue
            if proto in ("TCP", "UDP") and proto not in protocols:
                protocols.append(proto)
        if not protocols:
            protocols = ["TCP", "UDP"]

        from agent.diagnostic_ports import lookup_device, password_candidates, resolve_diagnostic_route

        dev = lookup_device(device_id=int(options.get("device_id") or 0), ip=ip)
        if not strict_ports:
            route_ctx = resolve_diagnostic_route(device=dev, configured_port=(ports[0] if ports else None), strict_port=False, extra_ports=tuple(ports))
            route = dict(route_ctx.get("route") or {})
            ports = list(route_ctx.get("candidate_ports") or ports)
            self.stdout.write(
                "Route resolution: "
                f"effective_port={route_ctx.get('effective_port')} route_status={route.get('route_status')} candidates={ports}"
            )

        from agent.plcommpro_bridge import (
            PlcommproConnInfo,
            bridge_available,
            connect_only,
        )

        if not bridge_available():
            self.stderr.write(
                "plcommpro bridge unavailable. Ensure env ZKACCESS_BRIDGE_EXE (preferred) or ZKACCESS_PYBRIDGE is set."
            )
            return

        pw_first = str(options.get("password") or "")
        candidates = password_candidates(supplied_password=pw_first, device=dev)

        self.stdout.write(f"IP={ip}")
        self.stdout.write(f"Ports={ports}")
        self.stdout.write(f"Protocols={protocols}")
        self.stdout.write(
            "Passwords="
            + ", ".join(["<blank>" if p == "" else p for p in candidates])
        )

        open_ports = [p for p in ports if self._tcp_open(ip, p, tcp_timeout)]
        self.stdout.write(f"TCP open ports: {open_ports}")
        if "TCP" in protocols and not open_ports:
            self.stderr.write("No TCP-open ports found in scan list (TCP attempts will be skipped).")

        found = False
        for proto in protocols:
            ports_to_try = open_ports if proto == "TCP" else ports
            if proto == "TCP" and not ports_to_try:
                continue
            for port in ports_to_try:
                for pw in candidates:
                    conn = PlcommproConnInfo(
                        ipaddress=ip,
                        ip_port=int(port),
                        password=str(pw),
                        timeout=int(timeout_ms),
                        protocol=str(proto),
                    )

                    rr = connect_only(conn, process_timeout_s=int(process_timeout_s))
                    ok = bool(rr.get("ok"))
                    dll = str(rr.get("dll_path_used") or "")
                    result = rr.get("result")
                    last_error = rr.get("last_error")
                    data = self._compact(rr.get("data"))
                    pw_label = "<blank>" if pw == "" else pw
                    self.stdout.write(
                        f"TRY proto={proto} port={port} pw={pw_label} -> ok={ok} result={result} last_error={last_error} dll={dll} data={data}"
                    )
                    if ok:
                        found = True
                        self.stdout.write(f"SUCCESS: proto={proto} port={port} pw={pw_label}")
                        return

                    # If the bridge timed out, try explicit DLL pinning across known repo candidates.
                    try:
                        if int(result or 0) == -500 and "timed out" in str(rr.get("data") or "").lower():
                            from agent.plcommpro_bridge import default_plcommpro_dll_path, _plcommpro_repo_candidates

                            dll_candidates = []
                            try:
                                d0 = str(default_plcommpro_dll_path() or "").strip()
                                if d0:
                                    dll_candidates.append(d0)
                            except Exception:
                                pass
                            try:
                                for d in _plcommpro_repo_candidates():
                                    ds = str(d or "").strip()
                                    if ds and ds not in dll_candidates:
                                        dll_candidates.append(ds)
                            except Exception:
                                pass

                            for pinned in dll_candidates:
                                try:
                                    rr2 = connect_only(
                                        conn,
                                        process_timeout_s=int(process_timeout_s),
                                        dll_path=str(pinned),
                                    )
                                    ok2 = bool(rr2.get("ok"))
                                    result2 = rr2.get("result")
                                    last_error2 = rr2.get("last_error")
                                    dll2 = str(rr2.get("dll_path_used") or pinned)
                                    data2 = self._compact(rr2.get("data"))
                                    self.stdout.write(
                                        f"PIN dll={dll2} -> ok={ok2} result={result2} last_error={last_error2} data={data2}"
                                    )
                                    if ok2:
                                        self.stdout.write(
                                            f"SUCCESS: proto={proto} port={port} pw={pw_label} dll={dll2}"
                                        )
                                        return
                                except Exception as e:
                                    self.stdout.write(
                                        f"PIN dll={pinned} -> exception={type(e).__name__}: {self._compact(str(e), max_len=200)}"
                                    )
                    except Exception:
                        pass

        if not found:
            self.stderr.write("No working combination found (TCP-open ports + UDP attempts on provided port list).")
