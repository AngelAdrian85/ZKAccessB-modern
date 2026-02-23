import json
import os
import re
import sys
from typing import Dict, List, Optional

from zkeco_modern.agent.plcommpro_bridge import modify_ip_udp, search_device_udp


def _parse_records(raw: str) -> List[Dict[str, str]]:
    raw = (raw or "").replace("\x00", "").strip()
    if not raw:
        return []
    recs = [r.strip() for r in re.split(r"[\r\n]+", raw) if r.strip()]
    out: List[Dict[str, str]] = []
    for rec in recs:
        parts = [p.strip() for p in rec.split(",") if p.strip()]
        d: Dict[str, str] = {"_raw": rec}
        for p in parts:
            if "=" not in p:
                continue
            k, v = p.split("=", 1)
            d[k.strip()] = v.strip()
        out.append(d)
    return out


def _find_by_ip(records: List[Dict[str, str]], ip: str) -> Optional[Dict[str, str]]:
    for r in records:
        if r.get("IP") == ip or r.get("IPAddress") == ip:
            return r
    return None


def main() -> int:
    target_ip = os.environ.get("ZK_TARGET_IP") or "192.168.1.220"

    resp = search_device_udp()
    if not resp.get("ok"):
        print(json.dumps(resp, indent=2), flush=True)
        return 2

    records = _parse_records(str(resp.get("data") or ""))
    rec = _find_by_ip(records, target_ip)
    if not rec:
        print(f"Device not found by UDP SearchDevice: ip={target_ip}")
        return 3

    mac = rec.get("MAC")
    netmask = rec.get("NetMask") or "255.255.255.0"
    gateway = rec.get("GATEIPAddress") or ""
    protype_before = rec.get("Protype") or ""

    if not mac:
        print("Missing MAC in SearchDevice record; cannot modify.")
        print(rec.get("_raw", ""))
        return 4

    if not gateway:
        # Best-effort default
        parts = target_ip.split(".")
        if len(parts) == 4:
            gateway = ".".join(parts[:3] + ["254"])

    payload = f"MAC={mac},IPAddress={target_ip},GATEIPAddress={gateway},NetMask={netmask},Protype=pull"

    print("[PULL] Found:", rec.get("_raw", ""), flush=True)
    print("[PULL] Sending ModifyIPAddress payload:", payload, flush=True)

    r2 = modify_ip_udp(payload)
    print("[PULL] ModifyIPAddress response:")
    print(json.dumps(r2, ensure_ascii=False, indent=2), flush=True)
    if not r2.get("ok"):
        return 5

    # Re-discover
    resp3 = search_device_udp()
    records3 = _parse_records(str(resp3.get("data") or ""))
    rec3 = _find_by_ip(records3, target_ip)
    if rec3:
        print("[PULL] After:", rec3.get("_raw", ""), flush=True)
        print(f"[PULL] Protype before={protype_before!r} after={(rec3.get('Protype') or '')!r}")
    else:
        print("[PULL] After: device not found by IP (might have rebooted / changed)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
