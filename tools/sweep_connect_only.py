from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict


def _filter_bad_syspath() -> None:
    bad_path_markers = ("ZKTeco", "python-support", "Python26")
    sys.path[:] = [p for p in sys.path if not (p and any(m in p for m in bad_path_markers))]


def _parse_ports(raw: str) -> list[int]:
    ports: list[int] = []
    for part in (raw or "").replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start = int(a.strip())
            end = int(b.strip())
            if end < start:
                start, end = end, start
            ports.extend(list(range(start, end + 1)))
        else:
            ports.append(int(part))
    # de-dup preserve order
    seen: set[int] = set()
    out: list[int] = []
    for p in ports:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out


def main() -> int:
    _filter_bad_syspath()
    repo_root = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, os.path.join(repo_root, "zkeco_modern"))

    from agent.plcommpro_bridge import PlcommproConnInfo, connect_only, default_plcommpro_dll_path

    ip = os.environ.get("ZK_IP", "192.168.1.235").strip()
    pw = os.environ.get("ZK_COMM_PASSWORD", "").strip()

    ports_raw = os.environ.get("ZK_PORTS", "4370,4371,4372,14370").strip()
    ports = _parse_ports(ports_raw)

    dll = (os.environ.get("ZK_DLL") or "").strip() or default_plcommpro_dll_path()
    if not dll:
        print("[FAIL] No plcommpro.dll found (set ZK_DLL or ZKACCESS_PLCOMMPRO_DLL)")
        return 2

    print("ip:", ip)
    print("ports:", ports)
    print("password set:", bool(pw))
    print("dll:", dll)

    results: dict[int, dict] = {}
    for port in ports:
        conn = PlcommproConnInfo(ipaddress=ip, ip_port=int(port), password=pw, timeout=8000, protocol="TCP")
        t0 = time.time()
        try:
            r = connect_only(conn, dll_path=dll, process_timeout_s=15)
        except Exception as e:
            r = {"ok": False, "exc": str(e)}
        r = {**r, "elapsed_s": round(time.time() - t0, 2), "port": port}
        results[port] = r
        ok = bool(r.get("ok"))
        code = r.get("last_error", r.get("result"))
        print(f"port {port}: ok={ok} code={code} elapsed={r['elapsed_s']}s")
        if ok:
            break

    print("\nJSON:")
    print(json.dumps(results, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
