"""Set push/ADMS WebServer URL for a ZKTeco controller via UDP ModifyIPAddress.

This is useful when the panel is stuck in `Protype=push` and PullSDK won't connect,
so we pivot to observing its push callbacks.

Usage (PowerShell):
  $env:ZK_TARGET_IP = '192.168.1.235'
  .\.venv\Scripts\python.exe scripts\set_push_server_udp.py --server-url http://192.168.1.2:8088

Optional:
  --broadcast 192.168.1.255
  --server-ip 192.168.1.2
  --server-port 8088
"""

from __future__ import annotations

import argparse
import os
import re
import time
from ipaddress import IPv4Address
from urllib.parse import urlsplit

from zkeco_modern.agent.plcommpro_bridge import modify_ip_udp, search_device_udp


def _find_record(raw: str, target_ip: str) -> str | None:
    raw = (raw or "").replace("\x00", "")
    recs = [r.strip() for r in re.split(r"[\r\n]+", raw) if r.strip()]
    for rec in recs:
        if f"IP={target_ip}" in rec or f"IPAddress={target_ip}" in rec:
            return rec
    return None


def _parse_kv(rec: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in (rec or "").split(","):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _directed_broadcast(ip: str, netmask: str) -> str:
    ip_i = int(IPv4Address(ip))
    mask_i = int(IPv4Address(netmask))
    bcast_i = (ip_i & mask_i) | (~mask_i & 0xFFFFFFFF)
    return str(IPv4Address(bcast_i))


def _search_any(broadcast: str) -> str:
    return str(search_device_udp(broadcast).get("data") or "")


def _rediscover(*, target_ip: str, broadcasts: list[str], timeout_s: float = 30.0) -> str | None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        for bcast in broadcasts:
            raw = _search_any(bcast)
            rec = _find_record(raw, target_ip)
            if rec:
                return rec
        time.sleep(1.5)
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-ip", default=os.environ.get("ZK_TARGET_IP", "192.168.1.235"))
    ap.add_argument("--broadcast", default=os.environ.get("ZK_BROADCAST", "192.168.1.255"))
    ap.add_argument("--server-url", required=True)
    ap.add_argument("--server-ip", default="")
    ap.add_argument("--server-port", type=int, default=0)
    ns = ap.parse_args()

    # If caller passes a full URL (recommended), infer server IP/port defaults.
    try:
        parsed = urlsplit(ns.server_url)
        if not ns.server_ip and parsed.hostname:
            ns.server_ip = parsed.hostname
        if not ns.server_port and parsed.port:
            ns.server_port = int(parsed.port)
    except Exception:
        pass
    if not ns.server_port:
        ns.server_port = 8088

    before_raw = _search_any(ns.broadcast)
    before = _find_record(before_raw, ns.target_ip)
    print("BEFORE:", before)
    if not before:
        return 2

    fields = _parse_kv(before)
    mac = fields.get("MAC")
    netmask = fields.get("NetMask") or "255.255.255.0"
    gw = fields.get("GATEIPAddress") or ""
    if not mac:
        print("Missing MAC in record")
        return 3

    directed_bcast = _directed_broadcast(ns.target_ip, netmask)
    broadcasts = [directed_bcast, ns.broadcast, "255.255.255.255"]
    print("BCASTS:", ", ".join(broadcasts))

    parts = [
        f"MAC={mac}",
        f"IPAddress={ns.target_ip}",
        f"NetMask={netmask}",
    ]
    if gw:
        parts.append(f"GATEIPAddress={gw}")

    # Web server / ADMS push settings
    parts.append(f"WebServerURL={ns.server_url}")
    if ns.server_ip:
        parts.append(f"WebServerIP={ns.server_ip}")
    parts.append(f"WebServerPort={int(ns.server_port)}")

    # keep current protype if present; default to push
    parts.append(f"Protype={fields.get('Protype') or 'push'}")

    payload = ",".join(parts)
    print("PAYLOAD:", payload)

    resp = modify_ip_udp(payload, directed_bcast)
    if not resp.get("ok"):
        resp = modify_ip_udp(payload, ns.broadcast)
    print("MODIFY:", resp)

    print("Waiting for rediscovery...")
    after = _rediscover(target_ip=ns.target_ip, broadcasts=broadcasts, timeout_s=30.0)
    print("AFTER:", after)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
