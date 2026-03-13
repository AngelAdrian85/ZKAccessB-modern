"""Standalone route-aware diagnostic for controller table/options behavior."""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DJANGO_SETTINGS_MODULE"] = "zkeco_config.settings"

import django

django.setup()

from agent.diagnostic_ports import resolve_diagnostic_route
from agent.drivers.plcommpro_bridge_driver import PlcommproBridgeDriver
from agent.models import Device
from agent.plcommpro_bridge import PlcommproConnInfo, get_device_options


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Route-aware full diagnostic for a controller")
    parser.add_argument("--device-id", type=int, default=22)
    parser.add_argument("--wait-seconds", type=int, default=15)
    parser.add_argument("--strict-port", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    dev = Device.objects.get(pk=int(args.device_id))
    drv = PlcommproBridgeDriver(dev)
    route_ctx = resolve_diagnostic_route(
        device=dev,
        configured_port=getattr(dev, "port", None),
        strict_port=bool(args.strict_port),
    )
    effective_port = int(route_ctx.get("effective_port") or getattr(dev, "port", 4370) or 4370)

    print(f"=== Device: {dev.ip_address}:{effective_port} (configured={dev.port}) ===")
    print(f"=== Route: {route_ctx.get('route')} ===")
    print()

    print(f"SCANEAZA CARDUL ACUM! (astept {int(args.wait_seconds)} secunde inainte de a incepe testele)")
    time.sleep(max(0, int(args.wait_seconds)))

    param_keys = (
        "CardAutoAdd,CardFmt,CardBitLen,WiegandFmtDef,WGFailedId,WGSiteCode,"
        "RFCardOn,OEMCode,RealTimeMonitor,CardViewMode,CardSendFullNo,"
        "RS232BaudRate,IPAddress,NetMask,GATEIPAddress,TCPPort,HTTPPort,Platform,FirmVer,Wiegand"
    )
    print("=== Device Parameters ===")
    resp = drv.get_options(param_keys)
    if int(resp.get("result", -1) or -1) >= 0:
        print("Options:", resp.get("data", ""))
    else:
        conn = PlcommproConnInfo(
            ipaddress=dev.ip_address,
            ip_port=effective_port,
            password=dev.comm_password or "0",
        )
        fallback = get_device_options(conn, param_keys)
        print("Options result:", fallback.get("result"), str(fallback.get("data", ""))[:500])

    print()
    table_names = [
        "wiegand",
        "oplog",
        "exlogdata",
        "alarmlog",
        "failedlog",
        "rfcardlog",
        "cardlog",
        "newlog",
        "realtime",
        "rtlog",
        "accesslog",
        "accessRecord",
        "cardRecord",
    ]
    print("=== Table scan (NewRecord) ===")
    for tbl in table_names:
        ret = drv.query_data(table=tbl, fields="*", option="NewRecord")
        result = ret.get("result", -99)
        data = ret.get("data", "")
        lines = [line.strip() for line in data.replace("\r\n", "\n").split("\n") if line.strip()]
        print(f"  table={tbl!r:20s}  result={result:4d}  lines={len(lines):3d}  preview={repr(data[:80])}")

    print()
    print("=== transaction KeepData (last 100) ===")
    ret = drv.query_data(
        table="transaction",
        fields="Cardno,Pin,Verified,DoorID,EventType,InOutState,Time_second,Index",
        option="KeepData",
    )
    print("  result:", ret.get("result"))
    data = ret.get("data", "")
    lines = [line.strip() for line in data.replace("\r\n", "\n").split("\n") if line.strip()]
    print("  lines:", len(lines))
    for line in lines[-10:]:
        print("  LINE:", repr(line))

    print()
    print("=== GetRTLog right now ===")
    ret = drv.get_rtlog()
    print("  result:", ret.get("result"))
    data = ret.get("data", "")
    for line in data.replace("\r\n", "\n").split("\n"):
        line = line.strip()
        if line:
            print("  RTLog:", repr(line))

    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
