from __future__ import annotations

import os
import sys
from dataclasses import dataclass


def _filter_bad_syspath() -> None:
    bad_path_markers = ("ZKTeco", "python-support", "Python26")
    sys.path[:] = [p for p in sys.path if not (p and any(m in p for m in bad_path_markers))]


@dataclass
class _Dev:
    ip_address: str
    port: int
    comm_password: str = ""


def main() -> int:
    _filter_bad_syspath()
    repo_root = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, os.path.join(repo_root, "zkeco_modern"))

    from agent.drivers.zk_socket_driver import ZKTechSocketDriver

    ip = os.environ.get("ZK_IP", "192.168.1.235").strip()
    ports_raw = os.environ.get("ZK_PORTS", "14370,4370,4371,4372,80,443").strip()
    ports = [int(p.strip()) for p in ports_raw.replace(";", ",").split(",") if p.strip()]

    passwords_raw = os.environ.get("ZK_PWS", ",0,12345").strip()
    passwords = [p.strip() for p in passwords_raw.replace(";", ",").split(",")]

    print("ip:", ip)
    print("ports:", ports)
    print("password candidates:", passwords)

    for port in ports:
        for pw in passwords:
            dev = _Dev(ip_address=ip, port=port, comm_password=pw)
            drv = ZKTechSocketDriver(dev)
            drv.timeout = 5.0
            r = drv.connect()
            ok = r.get("result") == 1
            print(f"port={port} pw={pw!r} -> {r}")
            try:
                drv.disconnect()
            except Exception:
                pass
            if ok:
                return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
