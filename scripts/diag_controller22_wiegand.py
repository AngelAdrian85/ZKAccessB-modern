from __future__ import annotations
# pyright: reportMissingImports=false

import argparse
import json
import os
import sys
import time
from typing import Iterable


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.join(REPO_ROOT, "zkeco_modern")
for path in (PROJECT_ROOT, REPO_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

bad_path_markers = ("ZKTeco", "python-support", "Python26")
sys.path[:] = [p for p in sys.path if not (p and any(marker in p for marker in bad_path_markers))]
os.environ["DJANGO_SETTINGS_MODULE"] = "zkeco_config.settings"

import django

django.setup()

from agent.controller_decoders import decode_transaction_rows, decode_user_rows
from agent.diagnostic_ports import resolve_diagnostic_route
from agent.drivers.plcommpro_bridge_driver import PlcommproBridgeDriver
from agent.models import Device


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe controller 22 for CardNo / raw Wiegand exposure during live scans.",
    )
    parser.add_argument("--device-id", type=int, default=22, help="Django device id to probe")
    parser.add_argument("--seconds", type=int, default=60, help="How long to poll after startup")
    parser.add_argument("--strict-port", action="store_true", help="Use configured port without route fallback")
    return parser


def has_raw_candidate(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    compact = text.replace(" ", "")
    return len(compact) >= 24 and len(compact) <= 80 and set(compact) <= {"0", "1"}


def preview_rows(rows: Iterable[dict]) -> list[dict]:
    return [row for row in rows][:5]


def load_panel_users(driver: PlcommproBridgeDriver) -> list[dict]:
    resp = driver.query_data(table="user", fields="Pin,CardNo,ViceCard,Group,Name", filter="", option="")
    if int(resp.get("result", -1) or -1) < 0:
        return []
    return decode_user_rows(resp.get("data") or "")


def print_json(label: str, payload: object) -> None:
    print(f"{label}: {json.dumps(payload, ensure_ascii=True, indent=2)}")


def main() -> int:
    args = build_parser().parse_args()
    device = Device.objects.get(pk=int(args.device_id))
    driver = PlcommproBridgeDriver(device)
    route_ctx = resolve_diagnostic_route(
        device=device,
        configured_port=getattr(device, "port", None),
        strict_port=bool(args.strict_port),
    )
    effective_port = int(route_ctx.get("effective_port") or getattr(device, "port", 4370) or 4370)

    print(f"Device: #{device.id} {device.ip_address}:{effective_port} configured={device.port}")
    print(f"Route: {route_ctx.get('route')}")
    print("Scan an unknown card now. Polling starts immediately.")
    print()

    option_keys = (
        "CardAutoAdd,CardFmt,CardBitLen,WiegandFmtDef,WGFailedId,WGSiteCode,"
        "RFCardOn,OEMCode,RealTimeMonitor,CardViewMode,CardSendFullNo,Platform,FirmVer,Wiegand"
    )
    try:
        options = driver.get_options(option_keys)
    except Exception as exc:
        options = {"result": -1, "error": str(exc)}
    print_json("DeviceOptions", options)

    try:
        panel_users = load_panel_users(driver)
    except Exception as exc:
        panel_users = []
        print(f"Panel user query failed: {exc}")
    print(f"Panel user rows: {len(panel_users)}")
    if panel_users:
        print_json("Panel user preview", preview_rows(panel_users))
    print()

    candidate_tables = ["wiegand", "rfcardlog", "cardlog", "newlog", "rtlog", "realtime", "accesslog"]
    seen_lines: set[str] = set()
    stats = {
        "rtlog_events": 0,
        "transaction_events": 0,
        "table_hits": 0,
        "cardno_present": 0,
        "raw_candidates": 0,
    }

    for tick in range(max(1, int(args.seconds))):
        stamp = time.strftime("%H:%M:%S")

        try:
            rt = driver.get_rtlog()
            data = str(rt.get("data") or "")
            for line in data.replace("\r\n", "\n").split("\n"):
                line = line.strip()
                if not line or line.lower().replace(" ", "").startswith("pin,verified") or line in seen_lines:
                    continue
                seen_lines.add(line)
                stats["rtlog_events"] += 1
                if has_raw_candidate(line):
                    stats["raw_candidates"] += 1
                print(f"[{stamp}] RTLOG {line!r}")
        except Exception as exc:
            print(f"[{stamp}] RTLOG error: {exc}")

        try:
            txn = driver.query_data(
                table="transaction",
                fields="Cardno,Pin,Verified,DoorID,EventType,InOutState,Time_second,Index",
                option="NewRecord",
            )
            rows = decode_transaction_rows(txn.get("data") or "")
            for row in rows:
                fingerprint = json.dumps(row, ensure_ascii=True, sort_keys=True)
                if fingerprint in seen_lines:
                    continue
                seen_lines.add(fingerprint)
                stats["transaction_events"] += 1
                if str(row.get("cardno") or "").strip():
                    stats["cardno_present"] += 1
                if any(has_raw_candidate(v) for v in row.values() if isinstance(v, str)):
                    stats["raw_candidates"] += 1
                print_json(f"[{stamp}] TRANSACTION", row)
        except Exception as exc:
            print(f"[{stamp}] TRANSACTION error: {exc}")

        if tick % 5 == 0:
            for table_name in candidate_tables:
                try:
                    result = driver.query_data(table=table_name, fields="*", option="NewRecord")
                    raw = str(result.get("data") or "")
                    lines = [line.strip() for line in raw.replace("\r\n", "\n").split("\n") if line.strip()]
                    if not lines:
                        continue
                    stats["table_hits"] += len(lines)
                    for line in lines[:5]:
                        if has_raw_candidate(line):
                            stats["raw_candidates"] += 1
                        print(f"[{stamp}] TABLE {table_name} {line!r}")
                except Exception as exc:
                    print(f"[{stamp}] TABLE {table_name} error: {exc}")

        time.sleep(1)

    print()
    print_json("Summary", stats)
    if stats["cardno_present"] <= 0:
        print("Conclusion: no live CardNo found during this capture window.")
    if stats["raw_candidates"] <= 0:
        print("Conclusion: no raw Wiegand-like payload detected in probed channels.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
