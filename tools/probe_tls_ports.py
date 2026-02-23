from __future__ import annotations

import os
import socket
import ssl


def _try_tls(ip: str, port: int, timeout: float = 5.0) -> dict:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        try:
            ss = ctx.wrap_socket(s, server_hostname=ip)
            cert = ss.getpeercert(binary_form=False)
            proto = ss.version()
            ss.close()
            return {"ok": True, "tls": True, "proto": proto, "cert_present": bool(cert)}
        except Exception as e:
            try:
                s.close()
            except Exception:
                pass
            return {"ok": False, "tls": False, "error": str(e)}
    except Exception as e:
        try:
            s.close()
        except Exception:
            pass
        return {"ok": False, "connect": False, "error": str(e)}


def main() -> int:
    ip = os.environ.get("ZK_IP", "192.168.1.235").strip()
    ports_raw = os.environ.get("ZK_PORTS", "443,14370").strip()
    ports = [int(p.strip()) for p in ports_raw.replace(";", ",").split(",") if p.strip()]

    print("ip:", ip)
    for p in ports:
        r = _try_tls(ip, p)
        print(f"port {p}: {r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
