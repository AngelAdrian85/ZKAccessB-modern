"""Live diagnostic: poll GetRTLog and transaction, print any new line found."""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'zkeco_config.settings'

import django
django.setup()

from agent.controller_decoders import decode_transaction_rows, decode_user_rows, preview_rows
from agent.drivers.plcommpro_bridge_driver import PlcommproBridgeDriver
from agent.diagnostic_ports import resolve_diagnostic_route
from agent.models import Device


def _load_panel_user_map(driver: PlcommproBridgeDriver) -> dict[str, dict[str, str]]:
    """Read panel-side user rows so live RTLOG PINs can be correlated to CardNo."""
    try:
        resp = driver.query_data(table='user', fields='Pin,CardNo,ViceCard,Group,Name', filter='', option='')
        if int(resp.get('result', -1) or -1) < 0:
            return {}
        rows = decode_user_rows(resp.get('data') or '')
    except Exception:
        return {}

    out: dict[str, dict[str, str]] = {}
    for row in rows:
        pin = str(row.get('pin') or '').strip()
        if not pin:
            continue
        out[pin] = {
            'cardno': str(row.get('cardno') or '').strip(),
            'vicecard': str(row.get('vicecard') or '').strip(),
            'group': str(row.get('group') or '').strip(),
            'name': str(row.get('name') or '').strip(),
        }
    return out


def _print_panel_match(panel_users: dict[str, dict[str, str]], pin: str) -> None:
    pin_txt = str(pin or '').strip()
    if not pin_txt:
        return
    info = panel_users.get(pin_txt)
    if not info:
        print(f"   panel_user_match=NONE for pin=[{pin_txt}]")
        return
    print(
        "   panel_user_match="
        f"pin=[{pin_txt}] cardno=[{info.get('cardno', '')}] vicecard=[{info.get('vicecard', '')}] "
        f"group=[{info.get('group', '')}] name=[{info.get('name', '')}]"
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Live route-aware RTLOG diagnostic")
    parser.add_argument("--device-id", type=int, default=22)
    parser.add_argument("--strict-port", action="store_true")
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument("--transaction-mode", choices=("off", "newrecord", "both"), default="off")
    parser.add_argument("--keepdata-every", type=int, default=10)
    parser.add_argument("--user-refresh-seconds", type=int, default=15)
    parser.add_argument("--timeout-ms", type=int, default=5000)
    parser.add_argument("--bridge-read-timeout-s", type=int, default=3)
    parser.add_argument("--bridge-control-timeout-s", type=int, default=3)
    parser.add_argument("--max-consecutive-errors", type=int, default=8)
    return parser.parse_args()


def _is_header_line(line: str) -> bool:
    return str(line or "").strip().lower().replace(" ", "").startswith("pin,verified")


def _iter_rtlog_lines(raw: str) -> list[str]:
    out: list[str] = []
    for line in str(raw or "").replace("\r\n", "\n").split("\n"):
        line = line.strip()
        if not line or _is_header_line(line):
            continue
        out.append(line)
    return out


def _result_error(resp: dict) -> str:
    return str(resp.get("error") or resp.get("data") or resp.get("note") or "unknown error").strip()


def _print_decoded_row(prefix: str, row: dict, panel_users: dict[str, dict[str, str]]) -> None:
    print(f"{prefix}: {row}")
    _print_panel_match(panel_users, row.get("pin", ""))


def _sleep_interruptible(seconds: float) -> None:
    remaining = max(0.0, float(seconds or 0.0))
    while remaining > 0:
        step = min(0.25, remaining)
        time.sleep(step)
        remaining -= step


def main() -> int:
    args = _parse_args()
    dev = Device.objects.get(pk=int(args.device_id))
    drv = PlcommproBridgeDriver(dev)
    drv.timeout_ms = max(1000, int(args.timeout_ms or 5000))
    bridge_read_timeout_s = max(2, int(args.bridge_read_timeout_s or 3))
    bridge_control_timeout_s = max(2, int(args.bridge_control_timeout_s or 3))
    drv._bridge_read_timeout_s = lambda: bridge_read_timeout_s
    drv._bridge_control_timeout_s = lambda: bridge_control_timeout_s
    route_ctx = resolve_diagnostic_route(
        device=dev,
        configured_port=getattr(dev, "port", None),
        strict_port=bool(args.strict_port),
    )
    effective_port = int(route_ctx.get("effective_port") or getattr(dev, "port", 4370) or 4370)

    poll_interval = max(0.2, float(args.poll_interval or 1.0))
    keepdata_every = max(0, int(args.keepdata_every or 0))
    refresh_every = max(0, int(args.user_refresh_seconds or 0))
    max_consecutive_errors = max(1, int(args.max_consecutive_errors or 8))
    duration_s = max(1, int(args.seconds or 1))
    transaction_mode = str(args.transaction_mode or "off").strip().lower()
    transaction_disabled_reason = ""

    print(f"Device: {dev.ip_address}:{effective_port} (configured={dev.port})")
    print(f"Route: {route_ctx.get('route')}")
    print("=" * 60)
    print("GATA - scaneaza cardul la centrala acum!")
    print(
        "Polling GetRTLog "
        f"la fiecare {poll_interval:.2f}s, transaction={transaction_mode}, "
        f"KeepData la {keepdata_every}s, refresh user map la {refresh_every}s, "
        f"bridge_timeout={bridge_read_timeout_s}s..."
    )
    print("=" * 60)

    panel_users = _load_panel_user_map(drv)
    print(f"Panel user map entries: {len(panel_users)}")
    sys.stdout.flush()

    seen_lines: set[str] = set()
    seen_rows: set[str] = set()
    stats = {
        "rtlog_lines": 0,
        "txn_rows": 0,
        "keepdata_rows": 0,
        "errors": 0,
        "panel_refreshes": 0,
    }
    consecutive_errors = 0
    started_at = time.monotonic()
    deadline = started_at + duration_s
    last_refresh_bucket = -1
    iteration = 0

    try:
        while True:
            timestamp = time.strftime("%H:%M:%S")
            iteration_had_error = False

            elapsed_s = int(time.monotonic() - started_at)
            if refresh_every and elapsed_s > 0:
                refresh_bucket = elapsed_s // refresh_every
            else:
                refresh_bucket = -1
            if refresh_every and refresh_bucket > 0 and refresh_bucket != last_refresh_bucket:
                last_refresh_bucket = refresh_bucket
                panel_users = _load_panel_user_map(drv)
                stats["panel_refreshes"] += 1
                print(f"[{timestamp}] panel_user_map refresh entries={len(panel_users)}")
                sys.stdout.flush()

            try:
                r = drv.get_rtlog()
                if int(r.get("result", -1) or -1) < 0:
                    iteration_had_error = True
                    stats["errors"] += 1
                    print(f"[{timestamp}] GetRTLog error: {_result_error(r)}")
                else:
                    for line in _iter_rtlog_lines(r.get("data", "")):
                        if line in seen_lines:
                            continue
                        seen_lines.add(line)
                        stats["rtlog_lines"] += 1
                        print(f"[{timestamp}] GetRTLog RAW: {repr(line)}")
                        decoded = preview_rows(decode_transaction_rows(line), max_rows=1)
                        if decoded:
                            row = decoded[0]
                            print(
                                "   decoded="
                                f"pin=[{row.get('pin', '')}] verified=[{row.get('verified', '')}] door=[{row.get('door_id', '')}] "
                                f"eventType=[{row.get('event_type', '')}] time=[{row.get('time_second') or row.get('time', '')}] "
                                f"index=[{row.get('index', '')}] cardno=[{row.get('cardno', '')}] format=[{row.get('source_format', '')}]"
                            )
                            _print_panel_match(panel_users, row.get("pin", ""))
                        sys.stdout.flush()
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                iteration_had_error = True
                stats["errors"] += 1
                print(f"[{timestamp}] GetRTLog exception: {exc}")

            if transaction_mode in {"newrecord", "both"}:
                try:
                    r2 = drv.query_data(
                        table="transaction",
                        fields="Cardno,Pin,Verified,DoorID,EventType,InOutState,Time_second,Index",
                        option="NewRecord",
                    )
                    if int(r2.get("result", -1) or -1) < 0:
                        iteration_had_error = True
                        stats["errors"] += 1
                        txn_error = _result_error(r2)
                        print(f"[{timestamp}] TXN error: {txn_error}")
                        if "accessviolationexception" in txn_error.lower():
                            transaction_mode = "off"
                            transaction_disabled_reason = "bridge AccessViolation on transaction/NewRecord"
                            print(f"[{timestamp}] TXN fallback disabled: {transaction_disabled_reason}")
                    else:
                        for row in decode_transaction_rows(r2.get("data", "")):
                            fingerprint = json.dumps(row, sort_keys=True, ensure_ascii=True)
                            if fingerprint in seen_rows:
                                continue
                            seen_rows.add(fingerprint)
                            stats["txn_rows"] += 1
                            _print_decoded_row(f"[{timestamp}] TXN decoded", row, panel_users)
                            sys.stdout.flush()
                except KeyboardInterrupt:
                    raise
                except Exception as exc:
                    iteration_had_error = True
                    stats["errors"] += 1
                    print(f"[{timestamp}] TXN exception: {exc}")

            if transaction_mode == "both" and keepdata_every and elapsed_s % keepdata_every == 0:
                try:
                    r3 = drv.query_data(table="transaction", fields="*", option="KeepData")
                    if int(r3.get("result", -1) or -1) < 0:
                        iteration_had_error = True
                        stats["errors"] += 1
                        keepdata_error = _result_error(r3)
                        print(f"[{timestamp}] TXN KeepData error: {keepdata_error}")
                        if "accessviolationexception" in keepdata_error.lower():
                            transaction_mode = "off"
                            transaction_disabled_reason = "bridge AccessViolation on transaction/KeepData"
                            print(f"[{timestamp}] TXN fallback disabled: {transaction_disabled_reason}")
                    else:
                        decoded3 = decode_transaction_rows(r3.get("data", ""))
                        new_count = 0
                        for row in decoded3:
                            fingerprint = json.dumps(row, sort_keys=True, ensure_ascii=True)
                            if fingerprint in seen_rows:
                                continue
                            seen_rows.add(fingerprint)
                            stats["keepdata_rows"] += 1
                            new_count += 1
                            _print_decoded_row("  KeepData ROW", row, panel_users)
                        print(f"[{timestamp}] TXN KeepData: {len(decoded3)} decoded rows, {new_count} new")
                        sys.stdout.flush()
                except KeyboardInterrupt:
                    raise
                except Exception as exc:
                    iteration_had_error = True
                    stats["errors"] += 1
                    print(f"[{timestamp}] TXN KeepData exception: {exc}")

            consecutive_errors = consecutive_errors + 1 if iteration_had_error else 0
            if consecutive_errors >= max_consecutive_errors:
                print(
                    f"[{timestamp}] Stop: reached {consecutive_errors} consecutive error iterations; "
                    "ending diagnostic early."
                )
                break

            iteration += 1
            remaining_s = deadline - time.monotonic()
            if remaining_s <= 0:
                break
            _sleep_interruptible(min(poll_interval, remaining_s))
    except KeyboardInterrupt:
        print("Diagnostic interrupted by user.")
    finally:
        runtime_s = time.monotonic() - started_at
        print("=" * 60)
        print(
            "Summary: "
            f"rtlog_lines={stats['rtlog_lines']} txn_rows={stats['txn_rows']} "
            f"keepdata_rows={stats['keepdata_rows']} errors={stats['errors']} "
            f"panel_refreshes={stats['panel_refreshes']} runtime_s={runtime_s:.1f}"
        )
        if transaction_disabled_reason:
            print(f"Transaction fallback disabled reason: {transaction_disabled_reason}")
        print("Terminat.")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
