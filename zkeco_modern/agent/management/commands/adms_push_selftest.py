from __future__ import annotations

import os
import time

from django.core.management.base import BaseCommand


def _truthy_env(v: str | None) -> bool:
    vv = str(v or "").strip().lower()
    if not vv:
        return False
    return vv not in ("0", "false", "no", "off")


def _guess_local_ip_for_device(device_ip: str) -> str:
    """Routing-based LAN IP guess: which local interface reaches device_ip."""
    try:
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((str(device_ip), 1))
        ip = str(s.getsockname()[0] or "").strip()
        s.close()
        return ip
    except Exception:
        return ""


class Command(BaseCommand):
    help = (
        "<30s self-test for ADMS/iClock push reachability. "
        "Optionally configures ServerAddr/ServerPort (direct or queued) and waits for "
        "real /iclock/getrequest or /iclock/cdata AuditLog entries."
    )

    def add_arguments(self, parser):
        parser.add_argument("--device-id", type=int, default=0, help="Device.id")
        parser.add_argument("--sn", type=str, default="", help="Device serial number")
        parser.add_argument("--seconds", type=float, default=30.0, help="Max wait time")

        parser.add_argument(
            "--apply",
            action="store_true",
            help="If set, apply ADMS ServerAddr/ServerPort before waiting.",
        )
        parser.add_argument(
            "--read-options",
            action="store_true",
            help="If set, enqueue GET_OPTION for ADMS keys via CommCenter and print latest audited values.",
        )
        parser.add_argument(
            "--read-options-items",
            default="ServerAddr,ServerPort,CLOUDSERVICEFLAG,ADMSServerIP",
            help=(
                "Comma-separated option names for GET_OPTION. "
                "Use ALL (or *) to request all options (if supported by device)."
            ),
        )
        parser.add_argument(
            "--reboot",
            action="store_true",
            help="Enqueue a REBOOT command via CommCenter (requires CommCenter running).",
        )
        parser.add_argument(
            "--server-addr",
            type=str,
            default="",
            help="Explicit server IP to set (default: route-to-device guess).",
        )
        parser.add_argument(
            "--server-port",
            type=int,
            default=0,
            help="Explicit server port to set (default: env ZKACCESS_ADMS_PORT).",
        )

    def handle(self, *args, **options):
        from agent.models import AuditLog, CommandLog, Device

        device_id = int(options.get("device_id") or 0)
        sn = str(options.get("sn") or "").strip()

        dev = None
        if device_id:
            dev = Device.objects.filter(id=device_id).first()
        if dev is None and sn:
            dev = Device.objects.filter(serial_number=sn).first()
        if dev is None:
            raise SystemExit("Device not found. Use --device-id or --sn.")

        device_id = int(dev.id)
        device_ip = str(getattr(dev, "ip_address", "") or "").strip()

        seconds = float(options.get("seconds") or 30.0)
        seconds = max(1.0, min(120.0, seconds))

        apply = bool(options.get("apply"))
        read_options = bool(options.get("read_options"))
        read_options_items = str(options.get("read_options_items") or "")
        if read_options_items.strip().upper() in {"ALL", "*"}:
            read_options_items = ""
        reboot = bool(options.get("reboot"))

        server_addr = str(options.get("server_addr") or "").strip()
        if not server_addr and device_ip:
            server_addr = _guess_local_ip_for_device(device_ip)

        server_port = int(options.get("server_port") or 0)
        if not server_port:
            try:
                server_port = int(str(os.environ.get("ZKACCESS_ADMS_PORT") or "0").strip() or "0")
            except Exception:
                server_port = 0

        self.stdout.write(
            f"Device: id={device_id} sn={getattr(dev, 'serial_number', '')} ip={device_ip} enabled={getattr(dev, 'enabled', None)}"
        )

        items_used = ""
        if apply:
            if not server_addr or server_addr.startswith("127."):
                raise SystemExit("Cannot apply: server_addr missing/loopback. Pass --server-addr.")
            if server_port <= 0 or server_port > 65535:
                raise SystemExit("Cannot apply: server_port invalid. Pass --server-port or set ZKACCESS_ADMS_PORT.")

            items_used = (
                f"ServerAddr={server_addr},ServerPort={int(server_port)},"
                f"CLOUDSERVICEFLAG=1,ADMSServerIP={server_addr},"
                f"WebServerURL=http://{server_addr}:{int(server_port)},"
                f"TransFlag=1,Realtime=1,RTLog=1,TransInterval=1"
            )

            # Try direct bridge first (works when CommCenter is NOT holding the device connection).
            direct_ok = False
            direct_err = ""
            try:
                from agent.plcommpro_bridge import PlcommproConnInfo, set_device_options

                conn = PlcommproConnInfo(
                    ipaddress=str(getattr(dev, "ip_address", "") or ""),
                    ip_port=int(getattr(dev, "port", 4370) or 4370),
                    password=str(getattr(dev, "comm_password", "") or ""),
                    timeout=4000,
                )
                resp = set_device_options(conn, items_used)
                direct_ok = bool(resp.get("ok"))
                if not direct_ok:
                    direct_err = str(resp.get("last_error") or resp.get("result") or "direct-failed")
            except Exception as e:
                direct_ok = False
                direct_err = str(e)

            if direct_ok:
                self.stdout.write(f"Applied directly via bridge: ServerAddr={server_addr} ServerPort={server_port}")
            else:
                if direct_err:
                    self.stdout.write(f"Direct apply unavailable ({direct_err}); falling back to queue via CommCenter")

                # Queue SET_OPTION: (works while CommCenter holds the connection).
                CommandLog.objects.filter(
                    device=dev,
                    status="PENDING",
                    command__startswith="SET_OPTION:ServerAddr=",
                ).delete()
                row = CommandLog.objects.create(device=dev, command=f"SET_OPTION:{items_used}", status="PENDING")
                self.stdout.write(
                    f"Queued: CommandLog id={row.id} SET_OPTION ServerAddr={server_addr} ServerPort={server_port}"
                )

        if read_options:
            opt_cmd_id = 0
            baseline_audit_id = 0
            try:
                baseline_audit_id = (
                    AuditLog.objects.filter(module="device", action="get_options", entity_id=device_id)
                    .order_by("-id")
                    .values_list("id", flat=True)
                    .first()
                    or 0
                )
                row = CommandLog.objects.create(
                    device=dev,
                    command=f"GET_OPTION:{read_options_items}",
                    status="PENDING",
                )
                opt_cmd_id = int(row.id)
                self.stdout.write(f"Enqueued GET_OPTION via CommCenter (CommandLog id={opt_cmd_id})")
            except Exception as e:
                self.stdout.write(f"Could not enqueue GET_OPTION: {e}")
                opt_cmd_id = 0
                baseline_audit_id = 0

        reboot_cmd_id = 0
        if reboot:
            try:
                row = CommandLog.objects.create(device=dev, command="REBOOT", status="PENDING")
                reboot_cmd_id = int(row.id)
                self.stdout.write(f"Enqueued REBOOT via CommCenter (CommandLog id={reboot_cmd_id})")
            except Exception as e:
                self.stdout.write(f"Could not enqueue REBOOT: {e}")
                reboot_cmd_id = 0

        start = time.time()
        try:
            last_id = int(
                AuditLog.objects.filter(module="iclock", entity_id=device_id)
                .order_by("-id")
                .values_list("id", flat=True)
                .first()
                or 0
            )
        except Exception:
            last_id = 0

        self.stdout.write(f"Waiting up to {seconds:.0f}s for device push/poll (AuditLog.module=iclock)…")

        deadline = start + seconds
        while time.time() < deadline:
            try:
                hit = (
                    AuditLog.objects.filter(
                        module="iclock",
                        entity_id=device_id,
                        id__gt=last_id,
                        action__in=("getrequest.poll", "getrequest.serve", "cdata"),
                    )
                    .order_by("id")
                    .first()
                )
            except Exception:
                hit = None

            if hit is not None:
                age = time.time() - start
                self.stdout.write(
                    f"PASS in {age:.1f}s: action={hit.action} ip={getattr(hit, 'ip_address', None) or ''}"
                )
                if items_used:
                    self.stdout.write(f"Applied/queued items: {items_used}")
                return

            time.sleep(0.25)

        self.stdout.write("FAIL: no iclock AuditLog received in time.")
        if items_used:
            self.stdout.write(f"Applied/queued items: {items_used}")

        hints: list[str] = []
        hints.append("Device not configured for ADMS push (ServerAddr/ServerPort/CLOUDSERVICEFLAG)")
        hints.append("Windows Firewall or network ACL blocks inbound TCP to server port")
        hints.append("Server bound to different port than device uses")
        if not device_ip:
            hints.append("Device.ip_address missing in DB (cannot route-guess server IP)")
        if server_addr and server_addr.startswith("127."):
            hints.append("ServerAddr resolved to 127.* (device cannot reach loopback)")

        self.stdout.write("Hints:")
        for h in hints:
            self.stdout.write(f"- {h}")

        # Extra visibility: show the newest iclock audit rows (if any)
        try:
            recent = list(
                AuditLog.objects.filter(module="iclock", entity_id=device_id).order_by("-id")[:5]
            )
        except Exception:
            recent = []
        if recent:
            self.stdout.write("Recent iclock AuditLog:")
            for a in reversed(recent):
                self.stdout.write(
                    f"- id={a.id} ts={getattr(a, 'timestamp', None)} action={a.action} ip={getattr(a, 'ip_address', None) or ''}"
                )

        if read_options:
            # Wait briefly for the GET_OPTION row to be executed, then print its audited details.
            opt_cmd_id = locals().get('opt_cmd_id', 0) or 0
            baseline_audit_id = locals().get('baseline_audit_id', 0) or 0
            if opt_cmd_id:
                t0 = time.time()
                while time.time() - t0 < 10.0:
                    try:
                        st = (
                            CommandLog.objects.filter(id=int(opt_cmd_id))
                            .values_list('status', flat=True)
                            .first()
                        )
                    except Exception:
                        st = None
                    if st and str(st) != 'PENDING' and str(st) != 'RUNNING':
                        break
                    time.sleep(0.25)

            opt = None
            # Wait for a *new* audit row (created asynchronously after CommandLog status update).
            t1 = time.time()
            while time.time() - t1 < 10.0:
                try:
                    opt = (
                        AuditLog.objects.filter(
                            module="device",
                            action="get_options",
                            entity_id=device_id,
                            id__gt=int(baseline_audit_id or 0),
                        )
                        .order_by("-id")
                        .first()
                    )
                except Exception:
                    opt = None
                if opt is not None:
                    break
                time.sleep(0.25)

            if opt is None:
                try:
                    opt = (
                        AuditLog.objects.filter(module="device", action="get_options", entity_id=device_id)
                        .order_by("-id")
                        .first()
                    )
                except Exception:
                    opt = None
            if opt is not None:
                self.stdout.write("Latest audited GET_OPTION:")
                details = str(getattr(opt, "details", "") or "").replace("\r\n", "\n").replace("\r", "\n")
                self.stdout.write(details[:1200])

        if reboot_cmd_id:
            # Wait briefly for the reboot command to be picked up.
            t0 = time.time()
            st = None
            while time.time() - t0 < 15.0:
                try:
                    st = (
                        CommandLog.objects.filter(id=int(reboot_cmd_id))
                        .values_list('status', flat=True)
                        .first()
                    )
                except Exception:
                    st = None
                if st and str(st) != 'PENDING' and str(st) != 'RUNNING':
                    break
                time.sleep(0.25)
            if st:
                self.stdout.write(f"REBOOT CommandLog status={st}")
