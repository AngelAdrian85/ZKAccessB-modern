"""Login to ZKTeco Webserver UI and call /cgi-bin/param.cgi commands.

Reads creds from env:
  ZKACCESS_WEB_USER
  ZKACCESS_WEB_PASSWORD

Prints responses for a few known commands.
"""

from __future__ import annotations

import base64
import hashlib
import os
import ssl
import sys
import json
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin
from urllib.request import HTTPCookieProcessor, HTTPSHandler, Request, build_opener


def build_opener_insecure():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    import http.cookiejar as cookiejar

    jar = cookiejar.CookieJar()
    op = build_opener(HTTPSHandler(context=ctx), HTTPCookieProcessor(jar))
    return ctx, op


def request(op, url: str, *, method: str = "GET", data: bytes | None = None, headers: dict[str, str] | None = None, timeout: float = 8.0):
    req = Request(url, data=data, method=method, headers=headers or {})
    try:
        with op.open(req, timeout=timeout) as resp:
            raw = resp.read() or b""
            status = int(getattr(resp, "status", 200))
        return status, raw
    except HTTPError as e:
        raw = b""
        try:
            raw = e.read() or b""
        except Exception:
            pass
        return int(getattr(e, "code", 0) or 0), raw


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: probe_zkteco_param_cgi.py <base_url> [cmd|json-payload ...]")
        return 2

    base = sys.argv[1].strip()
    if not base.endswith("/"):
        base += "/"

    username = (os.environ.get("ZKACCESS_WEB_USER") or "").strip()
    password = (os.environ.get("ZKACCESS_WEB_PASSWORD") or "").strip()
    if not username or not password:
        print("Missing creds: set ZKACCESS_WEB_USER and ZKACCESS_WEB_PASSWORD")
        return 3

    ctx, op = build_opener_insecure()
    origin = base.rstrip("/")

    login_url = urljoin(base, "cgi-bin/login.cgi")
    u64 = base64.b64encode(username.encode("utf-8")).decode("ascii")
    md5 = hashlib.md5(password.encode("utf-8")).hexdigest()

    login_body = urlencode({"-username": u64, "-userpass": md5}).encode("utf-8")
    status, raw = request(
        op,
        login_url,
        method="POST",
        data=login_body,
        headers={
            "User-Agent": "zkprobe",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": origin,
            "Referer": origin + "/login.html",
        },
    )
    txt = raw.decode("utf-8", "replace").strip().replace("\r", " ").replace("\n", " ")
    print(f"login status={status} head={txt[:200]}")
    if status != 200 or "Success" not in txt:
        print("Login failed; cannot call param.cgi")
        return 4

    param_url = urljoin(base, "cgi-bin/param.cgi")

    payload_args = sys.argv[2:]
    default_payloads = [
        {"cmd": "getdeviceinfo"},
        {"cmd": "getnetattr"},
        {"cmd": "getnetportattr"},
        {"cmd": "getpushserverattr"},
        {"cmd": "getdevlevel"},
        {"cmd": "getcommpwd"},
        {"cmd": "getdatapwd"},
    ]

    payloads = []
    if payload_args:
        for raw_arg in payload_args:
            raw_arg = (raw_arg or "").strip()
            if not raw_arg:
                continue
            if raw_arg.startswith("{"):
                try:
                    decoded = json.loads(raw_arg)
                except Exception as exc:
                    print(f"Invalid JSON payload: {raw_arg} ({exc})")
                    return 5
                if not isinstance(decoded, dict) or not decoded.get("cmd"):
                    print(f"Invalid payload (missing cmd): {raw_arg}")
                    return 5
                payloads.append({str(k): str(v) for k, v in decoded.items()})
            else:
                payloads.append({"cmd": raw_arg})
    else:
        payloads = default_payloads

    def call_payload(payload: dict[str, str]):
        body = urlencode(payload).encode("utf-8")
        st, rr = request(
            op,
            param_url,
            method="POST",
            data=body,
            headers={
                "User-Agent": "zkprobe",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "*/*",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": origin,
                "Referer": origin + "/main.html",
            },
        )
        tt = rr.decode("utf-8", "replace")
        print("\n== param.cgi payload=", payload, "status=", st)
        print(tt[:4000])

    for payload in payloads:
        call_payload(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
