import json

from django.core.management.base import BaseCommand, CommandError

from agent.controller_provisioning import (
    DEFAULT_TABLES,
    ProvisionTarget,
    bind_controller,
    discover_controller,
    probe_writeability,
    snapshot_controller,
)
from agent.diagnostic_ports import get_default_comm_password
from agent.models import Device


class Command(BaseCommand):
    help = (
        "Unified controller provisioning flow: discovery, identify, option snapshot, "
        "table support probe, writeability probe, and optional bind into the app."
    )

    def add_arguments(self, parser):
        parser.add_argument("--device-id", type=int, default=0, help="Load target IP/port/password from an existing Device row")
        parser.add_argument("--ip", type=str, default="", help="Target controller IP")
        parser.add_argument("--port", type=int, default=4370, help="Requested controller port; TCP provisioning auto-retries 14370/4370 candidates when needed")
        parser.add_argument("--password", type=str, default="", help="Controller comm password")
        parser.add_argument("--timeout-ms", type=int, default=3000, help="Bridge timeout in ms")
        parser.add_argument("--protocol", type=str, default="TCP", choices=["TCP", "UDP"], help="Protocol hint")
        parser.add_argument("--discover-base", type=str, default="", help="Subnet base for UDP discovery, e.g. 192.168.1")
        parser.add_argument("--name", type=str, default="", help="Device name override when binding")
        parser.add_argument("--serial", type=str, default="", help="Serial override when binding")
        parser.add_argument("--bind", action="store_true", help="Persist/update the controller in Device + DeviceStatus")
        parser.add_argument("--clear-on-add", action="store_true", help="Set Device.clear_on_add when binding")
        parser.add_argument("--skip-write-probe", action="store_true", help="Skip the safe writeability probes")
        parser.add_argument("--format", type=str, default="json", choices=["json", "markdown"], help="Output format")

    def handle(self, *args, **options):
        report: dict[str, object] = {}
        dev = None
        device_id = int(options.get("device_id") or 0)
        if device_id > 0:
            try:
                dev = Device.objects.get(pk=device_id)
            except Device.DoesNotExist as exc:
                raise CommandError(f"Device {device_id} not found") from exc
            options["ip"] = str(getattr(dev, "ip_address", "") or "").strip()
            options["port"] = int(getattr(dev, "port", 4370) or 4370)
            options["password"] = str(getattr(dev, "comm_password", "") or "")
            options["protocol"] = "TCP" if str(getattr(dev, "comm_mode", "tcp") or "tcp").lower() == "tcp" else "UDP"
        if not str(options.get("password") or "").strip():
            options["password"] = get_default_comm_password()

        discover_base = str(options.get("discover_base") or "").strip()
        if discover_base:
            report["discovery"] = discover_controller(discover_base)

        ip = str(options.get("ip") or "").strip()
        if not ip:
            discovered = report.get("discovery") or {}
            devices = list((discovered or {}).get("devices") or []) if isinstance(discovered, dict) else []
            if len(devices) == 1:
                ip = str(devices[0].get("ip") or "").strip()
            elif devices:
                raise CommandError("Multiple devices discovered; pass --ip to choose one explicitly.")
            else:
                raise CommandError("Missing --ip and no discovered device available.")

        target = ProvisionTarget(
            ip=ip,
            port=int(options.get("port") or 4370),
            password=str(options.get("password") or ""),
            timeout_ms=int(options.get("timeout_ms") or 3000),
            protocol=str(options.get("protocol") or "TCP"),
        )

        snapshot = snapshot_controller(target, table_names=DEFAULT_TABLES)
        report["snapshot"] = snapshot
        if not bool(snapshot.get("options_ok")):
            raise CommandError(f"Option snapshot failed for {ip}:{target.port}")

        if not bool(options.get("skip_write_probe")):
            report["writeability"] = probe_writeability(target)

        if bool(options.get("bind")):
            report["bind"] = bind_controller(
                snapshot,
                name=str(options.get("name") or getattr(dev, "name", "") or ""),
                serial_number=str(options.get("serial") or getattr(dev, "serial_number", "") or ""),
                clear_on_add=bool(options.get("clear_on_add")),
                comm_password=str(options.get("password") or ""),
            )

        fmt = str(options.get("format") or "json").strip().lower()
        if fmt == "markdown":
            self.stdout.write(self._render_markdown(report))
        else:
            self.stdout.write(json.dumps(report, indent=2, ensure_ascii=False, default=str))

    def _render_markdown(self, report: dict[str, object]) -> str:
        lines: list[str] = ["# Controller Provisioning Report", ""]
        discovery = report.get("discovery") if isinstance(report.get("discovery"), dict) else None
        if discovery is not None:
            lines.append("## Discovery")
            lines.append(f"- ok: {bool(discovery.get('ok'))}")
            lines.append(f"- devices: {len(discovery.get('devices') or [])}")
            lines.append("")
        snapshot = report.get("snapshot") if isinstance(report.get("snapshot"), dict) else {}
        identify = snapshot.get("identify") if isinstance(snapshot, dict) else {}
        lines.append("## Identify")
        lines.append(f"- ip: {identify.get('ip')}")
        lines.append(f"- serial: {identify.get('serial_number')}")
        lines.append(f"- name: {identify.get('device_name')}")
        lines.append(f"- product: {identify.get('product')}")
        lines.append("")
        lines.append("## Tables")
        for row in list(snapshot.get("tables") or []):
            lines.append(
                f"- {row.get('table')}: supported={row.get('supported')} count_result={row.get('count_result')} query_result={row.get('query_result')}"
            )
        writeability = report.get("writeability") if isinstance(report.get("writeability"), dict) else None
        if writeability is not None:
            lines.append("")
            lines.append("## Writeability")
            lines.append(f"- datetime: {writeability.get('datetime')}")
            lines.append(f"- user_write: {writeability.get('user_write')}")
        bind = report.get("bind") if isinstance(report.get("bind"), dict) else None
        if bind is not None:
            lines.append("")
            lines.append("## Bind")
            lines.append(f"- device_id: {bind.get('device_id')}")
            lines.append(f"- created: {bind.get('created')}")
            lines.append(f"- door_capacity: {bind.get('door_capacity')}")
            lines.append(f"- doors_created: {bind.get('doors_created')}")
        return "\n".join(lines)