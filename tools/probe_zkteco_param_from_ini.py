from __future__ import annotations

import argparse
import base64
import configparser
import hashlib
import http.cookiejar
import json
import ssl
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, HTTPSHandler, Request, build_opener


def _request(opener, url: str, *, data: bytes, headers: dict[str, str], timeout: float):
    req = Request(url, data=data, headers=headers, method="POST")
    try:
        with opener.open(req, timeout=timeout) as resp:
            raw = resp.read() or b""
            return int(getattr(resp, "status", 200) or 200), raw
    except HTTPError as exc:
        raw = b""
        try:
            raw = exc.read() or b""
        except Exception:
            pass
        return int(getattr(exc, "code", 0) or 0), raw


def _load_creds(ini_path: Path) -> tuple[str, str]:
    cfg = configparser.ConfigParser()
    cfg.read(ini_path, encoding="utf-8")
    user = (cfg.get("controller_web", "web_user", fallback="") or "").strip()
    password = (cfg.get("controller_web", "web_password", fallback="") or "").strip()
    return user, password


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe ZKTeco param.cgi using creds stored in agent_controller.ini")
    parser.add_argument("base_url")
    parser.add_argument("payload", nargs="+", help="Command name or JSON payload, e.g. getoplog or '{\"cmd\":\"getoplog\",\"-index\":\"0\"}'")
    parser.add_argument("--ini", default="zkeco_modern/agent_controller.ini")
    parser.add_argument("--timeout", type=float, default=12.0)
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    ini_path = Path(args.ini)
    user, password = _load_creds(ini_path)
    print(f"creds_present={bool(user and password)} ini={ini_path}")
    if not user or not password:
        return 3

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    opener = build_opener(HTTPSHandler(context=ctx), HTTPCookieProcessor(http.cookiejar.CookieJar()))

    origin = base
    login_data = urlencode({
        "-username": base64.b64encode(user.encode("utf-8")).decode("ascii"),
        "-userpass": hashlib.md5(password.encode("utf-8")).hexdigest(),
    }).encode("utf-8")
    login_status, login_raw = _request(
        opener,
        f"{base}/cgi-bin/login.cgi",
        data=login_data,
        headers={
            "User-Agent": "zkprobe",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": origin,
            "Referer": f"{origin}/login.html",
        },
        timeout=args.timeout,
    )
    login_text = login_raw.decode("utf-8", "replace").replace("\r", " ").replace("\n", " ")
    print(f"login_status={login_status} login_success={'Success' in login_text} head={login_text[:160]}")
    if login_status != 200 or "Success" not in login_text:
        return 4

    for raw_payload in args.payload:
        payload: dict[str, str]
        if raw_payload.strip().startswith("{"):
            decoded = json.loads(raw_payload)
            payload = {str(k): str(v) for k, v in decoded.items()}
        else:
            payload = {"cmd": raw_payload.strip()}
        status, body_raw = _request(
            opener,
            f"{base}/cgi-bin/param.cgi",
            data=urlencode(payload).encode("utf-8"),
            headers={
                "User-Agent": "zkprobe",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "*/*",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": origin,
                "Referer": f"{origin}/main.html",
            },
            timeout=args.timeout,
        )
        text = body_raw.decode("utf-8", "replace")
        preview = text.replace("\r", " ").replace("\n", " | ")[:2000]
        print(f"payload={payload} status={status} len={len(text)}")
        print(preview)
        print("---")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
