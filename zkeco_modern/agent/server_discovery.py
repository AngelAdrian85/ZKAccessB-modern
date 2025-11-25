"""Network discovery scaffold for access controllers.

Scans a configurable subnet (CIDR) attempting to connect to a list of
known ports; successful sockets produce candidate device records.

Usage:
    from agent.server_discovery import discover_devices
    results = discover_devices("192.168.1.0/24", ports=[4370])
"""

import ipaddress
import socket
import concurrent.futures
from typing import List, Dict, Tuple

DEFAULT_PORTS = [4370, 80]


def _probe(ip: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((ip, port))
            return True
    except Exception:
        return False


def discover_devices(cidr: str, ports: List[int] | None = None, max_workers: int = 64) -> List[Dict]:
    """Scan a CIDR for open controller ports.

    Returns a list of {"ip": str, "port": int} dicts. Uses thread pool.
    """
    network = ipaddress.ip_network(cidr, strict=False)
    ports = ports or DEFAULT_PORTS
    hosts = [str(h) for h in network.hosts()]
    results: List[Dict] = []
    future_meta: Dict[concurrent.futures.Future, Tuple[str, int]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        for ip_str in hosts:
            for port in ports:
                fut = ex.submit(_probe, ip_str, port)
                future_meta[fut] = (ip_str, port)
        for fut in concurrent.futures.as_completed(future_meta):
            ip_str, port = future_meta[fut]
            try:
                if fut.result():
                    results.append({"ip": ip_str, "port": port})
            except Exception:
                # Ignore individual probe errors; treat as closed
                pass
    return results
