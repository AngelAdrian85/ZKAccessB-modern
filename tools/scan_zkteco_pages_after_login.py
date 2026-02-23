"""Login to ZKTeco Webserver UI and scan additional pages/JS for CGI endpoints.

Reads creds from env:
  ZKACCESS_WEB_USER
  ZKACCESS_WEB_PASSWORD

This is a diagnostic crawler bounded to a fixed page list.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
import ssl
import sys
from html.parser import HTMLParser
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin
from urllib.request import HTTPCookieProcessor, HTTPSHandler, Request, build_opener


class RefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() in {"script", "img", "iframe", "frame"}:
            src = (attrs_dict.get("src") or "").strip()
            if src:
                self.refs.append(src)
        if tag.lower() in {"link", "a"}:
            href = (attrs_dict.get("href") or "").strip()
            if href and not href.lower().startswith("javascript:"):
                self.refs.append(href)


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
        print("Usage: scan_zkteco_pages_after_login.py <base_url>")
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

    # login
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
    print(f"login status={status} head={txt[:120]}")
    if status != 200 or "Success" not in txt:
        print("Login failed")
        return 4

    pages = [
        "main.html",
        "header.html",
        "left.html",
        "net.html",
        # discovered from js/left.js
        "commpwd.html",
        "datapwd.html",
        "port.html",
        "serverset.html",
        "sys.html",
        "time.html",
        "devinfo.html",
        "auth.html",
        "certificate.html",
        "zone.html",
        "user.html",
        "monitor.html",
        "oplog.html",
        "masterslave.html",
        "pers_index.html",
        "wifi.html",
        "ddns.html",
    ]

    endpoint_re = re.compile(r"/cgi-bin/[^\s'\"]+")
    cmd_re = re.compile(r"\"cmd\"\s*:\s*\"([^\"]+)\"")

    endpoints: set[str] = set()
    cmds: set[str] = set()
    fetched: set[str] = set()

    def scan(content: str) -> list[str]:
        for m in endpoint_re.findall(content or ""):
            endpoints.add(m)
        for c in cmd_re.findall(content or ""):
            cmds.add(c)
        parser = RefParser()
        try:
            parser.feed(content)
        except Exception:
            return []
        return parser.refs

    # Fetch pages and immediate referenced JS/CSS (bounded)
    to_fetch: list[str] = [urljoin(base, p) for p in pages]
    refs: list[str] = []

    for u in to_fetch:
        st, rr = request(op, u, headers={"User-Agent": "zkprobe", "Referer": origin + "/main.html"})
        if st != 200:
            continue
        fetched.add(u)
        txt = rr.decode("utf-8", "replace")
        refs.extend(scan(txt))

    # Normalize refs into absolute URLs
    abs_refs: list[str] = []
    for r in refs:
        r = r.strip()
        if not r or r.startswith("#"):
            continue
        abs_refs.append(urljoin(base, r.lstrip("/")))

    # Fetch a bounded number of referenced assets
    uniq_refs: list[str] = []
    seen: set[str] = set()
    for u in abs_refs:
        if u in seen:
            continue
        seen.add(u)
        uniq_refs.append(u)

    for u in uniq_refs[:80]:
        st, rr = request(op, u, headers={"User-Agent": "zkprobe", "Referer": origin + "/main.html"})
        if st != 200:
            continue
        fetched.add(u)
        txt = rr.decode("utf-8", "replace")
        scan(txt)

    print(f"fetched {len(fetched)} resources")

    print("\nCGI endpoints:")
    for e in sorted(endpoints):
        print(" ", e)

    if cmds:
        print("\ncmd values found:")
        for c in sorted(cmds):
            print(" ", c)

    keywords = ("comm", "pwd", "encrypt", "key", "tcp", "port", "sdk", "acc")
    interesting = [e for e in sorted(endpoints) if any(k in e.lower() for k in keywords)]
    if interesting:
        print("\ninteresting endpoints (keywords):")
        for e in interesting:
            print(" ", e)

    interesting_cmds = [c for c in sorted(cmds) if any(k in c.lower() for k in keywords)]
    if interesting_cmds:
        print("\ninteresting cmd values (keywords):")
        for c in interesting_cmds:
            print(" ", c)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
