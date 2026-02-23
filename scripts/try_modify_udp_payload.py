import re
import time
from ipaddress import IPv4Address

from zkeco_modern.agent.plcommpro_bridge import modify_ip_udp, search_device_udp


def _find_record(raw: str, target_ip: str) -> str | None:
    raw = (raw or "").replace("\x00", "")
    recs = [r.strip() for r in re.split(r"[\r\n]+", raw) if r.strip()]
    for rec in recs:
        if f"IP={target_ip}" in rec or f"IPAddress={target_ip}" in rec:
            return rec
    return None


def _find_record_by_mac(raw: str, mac: str) -> str | None:
    raw = (raw or "").replace("\x00", "")
    recs = [r.strip() for r in re.split(r"[\r\n]+", raw) if r.strip()]
    for rec in recs:
        if f"MAC={mac}" in rec:
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


def _rediscover(
    *,
    target_ip: str,
    target_mac: str,
    broadcasts: list[str],
    timeout_s: float = 60.0,
    interval_s: float = 2.0,
) -> str | None:
    deadline = time.time() + timeout_s
    last_seen: str | None = None
    while time.time() < deadline:
        for bcast in broadcasts:
            raw = _search_any(bcast)
            rec = _find_record(raw, target_ip) or _find_record_by_mac(raw, target_mac)
            if rec:
                return rec
            last_seen = None
        time.sleep(interval_s)
    return last_seen


def main() -> int:
    target_ip = "192.168.1.235"

    # Initial discovery (directed broadcast guessed from /24; then refined once we parse NetMask)
    broadcast_guess = "192.168.1.255"
    before_raw = _search_any(broadcast_guess)
    before = _find_record(before_raw, target_ip)
    print("BEFORE:", before)
    if not before:
        return 2

    fields = _parse_kv(before)
    mac = fields.get("MAC")
    netmask = fields.get("NetMask") or "255.255.255.0"
    gw = fields.get("GATEIPAddress") or "192.168.1.254"
    if not mac:
        print("Missing MAC in record")
        return 3

    directed_bcast = _directed_broadcast(target_ip, netmask)
    broadcasts = [directed_bcast, broadcast_guess, "255.255.255.255"]
    print("BCASTS:", ", ".join(broadcasts))

    payload = (
        f"MAC={mac},IPAddress={target_ip},GATEIPAddress={gw},NetMask={netmask},"
        "WebServerURL=,WebServerPort=0,WebServerIP=0.0.0.0,Protype=pull"
    )
    print("PAYLOAD:", payload)
    # Send modify on directed broadcast first (best chance), fall back to /24 broadcast.
    modify_resp = modify_ip_udp(payload, directed_bcast)
    if not modify_resp.get("ok"):
        modify_resp = modify_ip_udp(payload, broadcast_guess)
    print("MODIFY:", modify_resp)

    print("Waiting for rediscovery (device may reboot)...")
    after = _rediscover(
        target_ip=target_ip,
        target_mac=mac,
        broadcasts=broadcasts,
        timeout_s=60.0,
        interval_s=2.0,
    )
    print("AFTER:", after)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
