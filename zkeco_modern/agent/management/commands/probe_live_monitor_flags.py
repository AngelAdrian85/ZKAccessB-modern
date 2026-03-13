from __future__ import annotations

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from agent.controller_capabilities import resolve_port_route
from agent.controller_decoders import parse_option_pairs
from agent.models import Device
from agent.plcommpro_bridge import PlcommproConnInfo, get_device_options


DEFAULT_OPTION_ITEMS = (
    "Realtime,RTLog,TransFlag,TransInterval,"
    "CardFmt,CardBitLen,WiegandFmtDef,WGFailedId,WGSiteCode"
)


def _coerce_positive_int(value: str) -> int | None:
    text = str(value or "").strip()
    if not text or not text.isdigit():
        return None
    try:
        number = int(text)
    except Exception:
        return None
    return number if number > 0 else None


def _summarize_wiegand_config(flag_values: dict[str, str]) -> dict[str, object]:
    card_fmt = str(flag_values.get("CardFmt") or "").strip()
    bit_len = _coerce_positive_int(flag_values.get("CardBitLen") or "")
    fmt_def = str(flag_values.get("WiegandFmtDef") or "").strip()
    wg_failed_id = str(flag_values.get("WGFailedId") or "").strip()
    wg_site_code = str(flag_values.get("WGSiteCode") or "").strip()

    if bit_len in (26, 34):
        mode = f"Wiegand {bit_len}"
        looks_ok = True
    elif bit_len is not None:
        mode = f"Wiegand {bit_len}"
        looks_ok = False
    elif card_fmt:
        mode = card_fmt
        looks_ok = ("26" in card_fmt) or ("34" in card_fmt)
    else:
        mode = ""
        looks_ok = False

    return {
        "card_format": card_fmt,
        "bit_length": bit_len,
        "format_definition": fmt_def,
        "failed_id": wg_failed_id,
        "site_code": wg_site_code,
        "mode_hint": mode,
        "looks_supported_for_unknown_card": looks_ok,
    }


def _route_aware_conn_for_device(dev, *, timeout_ms: int = 4000):
    password = str(getattr(dev, "comm_password", "") or "").strip()
    if not password:
        try:
            from agent.models import SystemSettings

            ss = SystemSettings.get_solo()
            password = str(getattr(ss, "default_comm_password", "") or "").strip()
        except Exception:
            password = ""
    if not password:
        try:
            password = str(getattr(settings, "ZKACCESS_DEFAULT_COMM_PASSWORD", "") or "").strip()
        except Exception:
            password = ""

    route = resolve_port_route(
        getattr(dev, "port", None),
        device_name=str(getattr(dev, "name", "") or ""),
        hardware_version=str(getattr(dev, "hardware_version", "") or ""),
        firmware_version=str(getattr(dev, "firmware_version", "") or ""),
    )
    conn = PlcommproConnInfo(
        ipaddress=str(getattr(dev, "ip_address", "") or ""),
        ip_port=int(route.get("effective_port") or getattr(dev, "port", 4370) or 4370),
        password=password,
        timeout=int(timeout_ms),
    )
    return conn, route


class Command(BaseCommand):
    help = "Read Realtime/RTLog/TransFlag from a controller and report whether live monitoring is active."

    def add_arguments(self, parser):
        parser.add_argument("--device-id", type=int, default=0, help="Device.id")
        parser.add_argument("--sn", type=str, default="", help="Device serial number")
        parser.add_argument("--timeout-ms", type=int, default=4000, help="Bridge timeout in milliseconds")
        parser.add_argument(
            "--items",
            type=str,
            default=DEFAULT_OPTION_ITEMS,
            help="Comma-separated controller options to read",
        )
        parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    def handle(self, *args, **options):
        device_id = int(options.get("device_id") or 0)
        sn = str(options.get("sn") or "").strip()
        timeout_ms = max(1000, int(options.get("timeout_ms") or 4000))
        items = str(options.get("items") or DEFAULT_OPTION_ITEMS).strip()
        fmt = str(options.get("format") or "text").strip().lower()

        dev = None
        if device_id > 0:
            dev = Device.objects.filter(id=device_id).first()
        if dev is None and sn:
            dev = Device.objects.filter(serial_number=sn).first()
        if dev is None:
            raise CommandError("Device not found. Use --device-id or --sn.")

        conn, route = _route_aware_conn_for_device(dev, timeout_ms=timeout_ms)
        resp = dict(get_device_options(conn, items) or {})
        option_pairs = parse_option_pairs(str(resp.get("data") or ""))
        requested_items = [part.strip() for part in items.split(",") if part.strip()]
        flag_values = {key: str(option_pairs.get(key) or "").strip() for key in requested_items}
        live_monitoring_active = all(flag_values.get(key) == "1" for key in ("Realtime", "RTLog", "TransFlag"))
        wiegand = _summarize_wiegand_config(flag_values)
        unknown_card_capture_ready = bool(live_monitoring_active and wiegand.get("looks_supported_for_unknown_card"))

        report = {
            "ok": bool(resp.get("ok")) or bool(option_pairs),
            "device_id": int(dev.id),
            "serial_number": str(getattr(dev, "serial_number", "") or ""),
            "ip_address": str(getattr(dev, "ip_address", "") or ""),
            "configured_port": int(getattr(dev, "port", 4370) or 4370),
            "effective_port": int(route.get("effective_port") or getattr(dev, "port", 4370) or 4370),
            "route_status": str(route.get("route_status") or ""),
            "transport": str(resp.get("transport") or "bridge"),
            "result": resp.get("result"),
            "items": flag_values,
            "missing_items": [key for key in requested_items if key not in option_pairs],
            "live_monitoring_active": live_monitoring_active,
            "wiegand": wiegand,
            "unknown_card_capture_ready": unknown_card_capture_ready,
            "raw": str(resp.get("data") or ""),
        }

        if fmt == "json":
            self.stdout.write(json.dumps(report, indent=2, ensure_ascii=True))
            return

        self.stdout.write(
            f"Device: id={report['device_id']} sn={report['serial_number']} ip={report['ip_address']} "
            f"configured_port={report['configured_port']} effective_port={report['effective_port']}"
        )
        self.stdout.write(f"Route: {report['route_status']} transport={report['transport']} result={report['result']}")
        for key in requested_items:
            value = flag_values.get(key, "")
            suffix = " (missing)" if key in report["missing_items"] else ""
            self.stdout.write(f"{key}={value or '-'}{suffix}")
        self.stdout.write(f"live_monitoring_active={'YES' if live_monitoring_active else 'NO'}")
        self.stdout.write(
            "wiegand_mode_hint="
            + (str(wiegand.get("mode_hint") or "-") if wiegand else "-")
        )
        self.stdout.write(
            "unknown_card_capture_ready="
            + ("YES" if unknown_card_capture_ready else "NO")
        )
        if not live_monitoring_active:
            self.stdout.write("Expected for active live monitoring: Realtime=1, RTLog=1, TransFlag=1")
        if not bool(wiegand.get("looks_supported_for_unknown_card")):
            self.stdout.write(
                "Reader Wiegand format is not clearly 26/34-bit; check CardFmt/CardBitLen/WiegandFmtDef."
            )