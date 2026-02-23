import argparse
import json

from zkeco_modern.agent.plcommpro_bridge import (
    PlcommproConnInfo,
    get_device_options,
    query_data,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe a ZKTeco panel via plcommpro.dll bridge")
    ap.add_argument("--ip", required=True)
    ap.add_argument("--port", type=int, default=4370)
    ap.add_argument("--password", default="")
    ap.add_argument("--timeout", type=int, default=3000)
    ap.add_argument("--options", default="NetMask,GATEIPAddress,IPAddress")
    ap.add_argument("--table", default="")
    ap.add_argument("--fields", default="*")
    ap.add_argument("--filter", default="")
    ap.add_argument("--option", default="")
    args = ap.parse_args()

    conn = PlcommproConnInfo(
        ipaddress=args.ip,
        ip_port=args.port,
        password=args.password,
        timeout=args.timeout,
    )

    out = {"ok": True, "options": None, "query": None}

    try:
        out["options"] = get_device_options(conn, args.options)
    except Exception as e:
        out["options"] = {"ok": False, "error": str(e)}

    if args.table:
        try:
            out["query"] = query_data(
                conn,
                table=args.table,
                fields=args.fields,
                filter=args.filter,
                option=args.option,
            )
        except Exception as e:
            out["query"] = {"ok": False, "error": str(e)}

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
