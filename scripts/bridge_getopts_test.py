import json
import os
import sys

from zkeco_modern.agent.plcommpro_bridge import PlcommproConnInfo, get_device_options


def main() -> int:
    ip = os.environ.get("ZK_TEST_IP") or "192.168.1.220"
    port = int(os.environ.get("ZK_TEST_PORT") or 4370)
    password = os.environ.get("ZK_TEST_PASS") or ""

    protocol = (os.environ.get("ZK_TEST_PROTOCOL") or os.environ.get("ZK_TEST_PROTO") or "").strip() or None

    conn = PlcommproConnInfo(ipaddress=ip, ip_port=port, password=password, timeout=3000, protocol=protocol)
    resp = get_device_options(conn, "IPAddress,NetMask,GATEIPAddress,WebServerURL,~SerialNumber")
    print(json.dumps(resp, ensure_ascii=False, indent=2))

    ok = bool(resp.get("ok"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
