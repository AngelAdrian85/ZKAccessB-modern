import json
import re
from datetime import datetime, timedelta
from typing import Any

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Minimal plcommpro bridge flow probe (connect -> params -> transaction NewRecord -> optional door open). "
        "Use this to validate bidirectional comm on real hardware."
    )

    def add_arguments(self, parser):
        parser.add_argument("--ip", type=str, required=True, help="Device IP (e.g. 192.168.1.235)")
        parser.add_argument("--port", type=int, default=4370, help="Device TCP port (e.g. 14370 or 4370)")
        parser.add_argument("--password", type=str, default="", help="Device comm password (often '0')")
        parser.add_argument("--timeout-ms", type=int, default=3000, help="SDK timeout in ms (default 3000)")
        parser.add_argument("--protocol", type=str, default="TCP", choices=["TCP", "UDP"], help="Protocol hint")

        parser.add_argument(
            "--raw",
            action="store_true",
            help="Print full raw payloads (can be large). Default prints short previews.",
        )
        parser.add_argument(
            "--no-newrecord",
            action="store_true",
            help="Disable NewRecord query; will count+optionally query full transaction table.",
        )

        parser.add_argument(
            "--tables",
            type=str,
            default="",
            help=(
                "Optional comma-separated extra table names to probe via data_count/query_data "
                "(e.g. 'transaction,rtlog,eventlog')."
            ),
        )

        parser.add_argument(
            "--door-open",
            action="store_true",
            help="Actually send door open command (ControlDevice op=1).",
        )
        parser.add_argument("--door", type=int, default=1, help="Door number for --door-open (default 1)")
        parser.add_argument("--index", type=int, default=1, help="Index for ControlDevice (default 1)")
        parser.add_argument("--state", type=int, default=1, help="State for ControlDevice (default 1=open)")

        parser.add_argument(
            "--write-probe",
            action="store_true",
            help=(
                "Run safe writeability probes (SetDeviceParam DateTime jump+restore, "
                "and SetDeviceData(user) count delta). Useful to detect read-only ports/firmware."
            ),
        )

    def _parse_kv_pairs(self, raw: str) -> dict[str, str]:
        s = (raw or "").replace("\x00", "").strip()
        if not s:
            return {}
        parts: list[str] = []
        for line in s.split("\r\n"):
            line = line.strip()
            if not line:
                continue
            parts.extend([p.strip() for p in line.split(",") if p.strip()])
        out: dict[str, str] = {}
        for p in parts:
            if "=" not in p:
                continue
            k, v = p.split("=", 1)
            out[k.strip()] = v.strip()
        return out

    def _coerce_datetime_value(self, value: str) -> tuple[str, str] | None:
        """Return (kind, normalized_value) for DateTime.

        Observed formats:
        - Integer seconds since 2000-01-01 on some C3-Pro firmware
        - "YYYY-MM-DD HH:MM:SS" on other devices
        """
        v = (value or "").strip()
        if not v:
            return None
        if re.fullmatch(r"\d+", v):
            return ("epoch2000", v)
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            return ("string", v)
        except ValueError:
            return None

    def _preview(self, raw: str, max_chars: int = 600, max_lines: int = 6) -> str:
        s = (raw or "").replace("\x00", "")
        if not s:
            return ""
        lines = [ln for ln in s.split("\r\n") if ln]
        head = "\r\n".join(lines[:max_lines])
        if len(head) > max_chars:
            head = head[:max_chars] + "..."
        if len(lines) > max_lines:
            head += f"\r\n... ({len(lines)} lines total)"
        return head

    def _dump_resp(self, title: str, resp: dict[str, Any], *, raw: bool = False):
        ok = bool(resp.get("ok"))
        result = resp.get("result")
        last_error = resp.get("last_error")
        dll = resp.get("dll_path_used")
        data = resp.get("data")

        self.stdout.write("\n" + ("=" * 72))
        self.stdout.write(f"{title}: ok={ok} result={result} last_error={last_error} dll={dll}")

        if isinstance(data, (dict, list)):
            self.stdout.write(json.dumps(data, indent=2, ensure_ascii=False) if raw else str(data)[:800])
            return

        text = str(data or "")
        if raw:
            self.stdout.write(text)
        else:
            self.stdout.write(self._preview(text) or "(empty)")

    def handle(self, *args, **options):
        ip: str = str(options["ip"] or "").strip()
        port: int = int(options["port"] or 0)
        password: str = str(options["password"] or "")
        timeout_ms: int = int(options["timeout_ms"] or 3000)
        protocol: str = str(options["protocol"] or "TCP").strip().upper()
        raw: bool = bool(options.get("raw"))

        from agent.plcommpro_bridge import (
            PlcommproConnInfo,
            bridge_available,
            control_device,
            data_count,
            get_device_options,
            set_device_options,
            query_data,
            set_device_data,
        )

        if not bridge_available():
            self.stderr.write(
                "plcommpro bridge unavailable. Ensure env ZKACCESS_BRIDGE_EXE (preferred) or ZKACCESS_PYBRIDGE is set."
            )
            return

        conn = PlcommproConnInfo(
            ipaddress=ip,
            ip_port=int(port),
            password=password,
            timeout=int(timeout_ms),
            protocol=protocol,
        )

        self.stdout.write(
            f"Probing plcommpro flow for {ip}:{port} (protocol={protocol}, timeout_ms={timeout_ms})"
        )

        # 1) Minimal admin-like params (GetDeviceParam via GetDeviceOptions items).
        items = "IPAddress,NetMask,GATEIPAddress,WebServerURL,~SerialNumber,DeviceName,Product"
        resp_opts = get_device_options(conn, items)
        self._dump_resp("get_device_options", resp_opts, raw=raw)

        # 2) Sanity: DataCount(transaction)
        resp_cnt = data_count(conn, "transaction")
        self._dump_resp("data_count(transaction)", resp_cnt, raw=raw)

        # 3) Near-realtime: NewRecord transaction query (legacy behavior)
        option = "" if bool(options.get("no_newrecord")) else "NewRecord"
        resp_new = query_data(conn, table="transaction", fields="*", option=option)
        self._dump_resp(f"query_data(transaction, option={option or 'NONE'})", resp_new, raw=raw)

        # 3b) Optional: probe arbitrary tables (count + preview)
        tables_raw = str(options.get("tables") or "").strip()
        if tables_raw:
            tables = [t.strip() for t in tables_raw.split(",") if t.strip()]
            # De-dup while preserving order
            seen = set()
            tables = [t for t in tables if not (t.lower() in seen or seen.add(t.lower()))]
            for table in tables:
                self._dump_resp(f"data_count({table})", data_count(conn, table), raw=raw)
                self._dump_resp(f"query_data({table})", query_data(conn, table=table, fields="*"), raw=raw)

        # 4) Optional: door open command (push)
        if bool(options.get("door_open")):
            door = int(options.get("door") or 1)
            index = int(options.get("index") or 1)
            state = int(options.get("state") or 1)
            self.stdout.write(
                f"\nSending ControlDevice(op=1) door={door} index={index} state={state}..."
            )
            resp_ctl = control_device(conn, door=door, index=index, state=state, time=0)
            self._dump_resp("control_device", resp_ctl, raw=raw)

        # 5) Optional: writeability probe
        if bool(options.get("write_probe")):
            self.stdout.write("\n" + ("=" * 72))
            self.stdout.write("write_probe: starting")

            # 5a) SetDeviceParam(DateTime) jump + restore
            resp_dt0 = get_device_options(conn, "DateTime")
            self._dump_resp("write_probe:get_device_options(DateTime)", resp_dt0, raw=True)
            kv0 = self._parse_kv_pairs(str(resp_dt0.get("data") or ""))
            dt0_val = kv0.get("DateTime", "")
            dt_kind = self._coerce_datetime_value(dt0_val)

            if not resp_dt0.get("ok") or not dt_kind:
                self.stdout.write("write_probe: DateTime unavailable or unparseable; skipping SetDeviceParam test")
            else:
                kind, norm = dt_kind
                if kind == "epoch2000":
                    base = int(norm)
                    target = base + 30
                    restore = base
                    self.stdout.write(f"write_probe: DateTime kind=epoch2000 base={base} target={target}")
                    resp_set = set_device_options(conn, f"DateTime={target}")
                    self._dump_resp("write_probe:set_device_options(DateTime=+30)", resp_set, raw=True)
                    resp_dt1 = get_device_options(conn, "DateTime")
                    self._dump_resp("write_probe:get_device_options(DateTime) after set", resp_dt1, raw=True)
                    resp_restore = set_device_options(conn, f"DateTime={restore}")
                    self._dump_resp("write_probe:restore DateTime", resp_restore, raw=True)
                else:
                    base_s = norm
                    try:
                        base_dt = datetime.strptime(base_s, "%Y-%m-%d %H:%M:%S")
                        target_s = (base_dt + timedelta(seconds=30)).strftime("%Y-%m-%d %H:%M:%S")
                        self.stdout.write(f"write_probe: DateTime kind=string base={base_s} target={target_s}")
                        resp_set = set_device_options(conn, f"DateTime={target_s}")
                        self._dump_resp("write_probe:set_device_options(DateTime=+30s)", resp_set, raw=True)
                        resp_dt1 = get_device_options(conn, "DateTime")
                        self._dump_resp("write_probe:get_device_options(DateTime) after set", resp_dt1, raw=True)
                        resp_restore = set_device_options(conn, f"DateTime={base_s}")
                        self._dump_resp("write_probe:restore DateTime", resp_restore, raw=True)
                    except Exception:
                        self.stdout.write("write_probe: failed to compute DateTime target; skipping")

            # 5b) SetDeviceData(user) count delta
            resp_user_before = data_count(conn, "user")
            self._dump_resp("write_probe:data_count(user) before", resp_user_before, raw=True)

            dummy = "\t".join(
                [
                    "Pin=999",
                    "CardNo=999999",
                    "Name=WRITE_PROBE",
                    "Group=1",
                    "StartTime=2000-01-01 00:00:00",
                    "EndTime=2099-12-31 23:59:59",
                ]
            )
            resp_set_user = set_device_data(conn, table="user", data=dummy, option="")
            self._dump_resp("write_probe:set_device_data(user)", resp_set_user, raw=True)

            resp_user_after = data_count(conn, "user")
            self._dump_resp("write_probe:data_count(user) after", resp_user_after, raw=True)

            # Best-effort cleanup; harmless if writes are no-op.
            from agent.plcommpro_bridge import delete_device_data

            resp_del = delete_device_data(conn, table="user", filter="Pin=999")
            self._dump_resp("write_probe:delete_device_data(user Pin=999)", resp_del, raw=True)

            self.stdout.write("write_probe: done")

        self.stdout.write("\nDone.")
