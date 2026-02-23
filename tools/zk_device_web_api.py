from __future__ import annotations

import argparse
import base64
import hashlib
import sys
from dataclasses import dataclass


def _b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def _md5_hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ZkWebTarget:
    scheme: str
    host: str
    port: int

    def url(self, path: str) -> str:
        path = path if path.startswith("/") else f"/{path}"
        return f"{self.scheme}://{self.host}:{self.port}{path}"


def _require_requests():
    try:
        import requests  # type: ignore

        return requests
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            "Missing dependency: requests. Install it with: pip install requests"
        ) from exc


def login(session, target: ZkWebTarget, username: str, password: str, timeout_s: float = 8.0) -> str:
    url = target.url("/cgi-bin/login.cgi")

    # Some firmware builds require browser-like headers or the CGI returns HTTP 500.
    session.headers.setdefault("User-Agent", "Mozilla/5.0")
    session.headers.setdefault("Accept", "*/*")
    session.headers.setdefault("X-Requested-With", "XMLHttpRequest")
    session.headers.setdefault("Origin", f"{target.scheme}://{target.host}")
    session.headers.setdefault("Referer", target.url("/login.html"))

    payload = {"-username": _b64(username), "-userpass": _md5_hex(password)}
    resp = session.post(url, data=payload, timeout=timeout_s)
    return resp.text


def param(session, target: ZkWebTarget, data: dict, timeout_s: float = 8.0) -> str:
    url = target.url("/cgi-bin/param.cgi")
    session.headers.setdefault("User-Agent", "Mozilla/5.0")
    session.headers.setdefault("Accept", "*/*")
    session.headers.setdefault("X-Requested-With", "XMLHttpRequest")
    session.headers.setdefault("Origin", f"{target.scheme}://{target.host}")
    session.headers.setdefault("Referer", target.url("/main.html"))

    resp = session.post(url, data=data, timeout=timeout_s)
    return resp.text


def disable_push_server(
    *,
    ip: str,
    username: str,
    password: str,
    scheme: str = "https",
    port: int = 443,
    serveraddr: str = "0.0.0.0",
    serverport: int = 0,
    reboot: bool = True,
    timeout_s: float = 8.0,
) -> int:
    requests = _require_requests()

    target = ZkWebTarget(scheme=scheme, host=ip, port=port)

    session = requests.Session()
    session.verify = False  # device uses self-signed certs frequently

    r_login = login(session, target, username, password, timeout_s=timeout_s)
    if "Success" not in (r_login or ""):
        print("[ERROR] Login failed. Response:")
        print(r_login)
        return 2
    print("[OK] Logged in")

    r_get = param(session, target, {"cmd": "getpushserverattr"}, timeout_s=timeout_s)
    print("[INFO] getpushserverattr:")
    print(r_get)

    # Firmware differs: some panels expect IP+port, others expect URL mode.
    r_set = param(
        session,
        target,
        {"cmd": "setpushserverattr", "-serveraddr": serveraddr, "-serverport": str(serverport)},
        timeout_s=timeout_s,
    )
    ok = "Success" in (r_set or "")
    if not ok:
        # Fallback: clear URL mode.
        r_set2 = param(
            session,
            target,
            {"cmd": "setpushserverattr", "-serverurl": ""},
            timeout_s=timeout_s,
        )
        ok = "Success" in (r_set2 or "")

    # Verify by re-reading settings, even if response is empty.
    r_get2 = param(session, target, {"cmd": "getpushserverattr"}, timeout_s=timeout_s)
    print("[INFO] getpushserverattr (after set):")
    print(r_get2)

    if (serveraddr in (r_get2 or "")) or ("WebServerIP=\"\"" in (r_get2 or "")) or ("WebServerURL=\"\"" in (r_get2 or "")):
        ok = True

    if not ok:
        print("[ERROR] setpushserverattr did not report success and verification did not change values.")
        print("[DEBUG] set response (ip mode):")
        print(r_set)
        return 3

    print(f"[OK] Push server cleared/set (target {serveraddr}:{serverport})")

    if reboot:
        r_reboot = param(session, target, {"cmd": "reboot"}, timeout_s=timeout_s)
        if "Success" not in (r_reboot or ""):
            print("[WARN] reboot command did not return Success. Response:")
            print(r_reboot)
            return 4
        print("[OK] Reboot triggered")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="ZKTeco controller web UI helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("disable-push", help="Disable push mode by clearing Push Server settings")
    p.add_argument("--ip", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--password", required=True)
    p.add_argument("--scheme", default="https", choices=["http", "https"])
    p.add_argument("--port", type=int, default=443)
    p.add_argument("--serveraddr", default="0.0.0.0")
    p.add_argument("--serverport", type=int, default=0)
    p.add_argument("--no-reboot", action="store_true")
    p.add_argument("--timeout", type=float, default=8.0)

    args = parser.parse_args(argv)

    if args.cmd == "disable-push":
        return disable_push_server(
            ip=args.ip,
            username=args.user,
            password=args.password,
            scheme=args.scheme,
            port=args.port,
            serveraddr=args.serveraddr,
            serverport=args.serverport,
            reboot=not args.no_reboot,
            timeout_s=args.timeout,
        )

    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
