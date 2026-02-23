"""Login to a ZKTeco Webserver UI and discover referenced /cgi-bin endpoints.

This is best-effort diagnostics. It tries to:
- login via /cgi-bin/login.cgi (POST)
- fetch a few landing pages
- collect JS/CSS references and search for /cgi-bin/* strings

Credentials are read from env by default:
  ZKACCESS_WEB_USER
  ZKACCESS_WEB_PASSWORD

Avoid passing passwords on the command line when possible.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
import ssl
import sys
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Iterable
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import HTTPCookieProcessor, HTTPSHandler, Request, build_opener


@dataclass
class FetchResult:
    url: str
    status: int
    text: str


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "script":
            src = (attrs_dict.get("src") or "").strip()
            if src:
                self.scripts.append(src)
        if tag.lower() == "link":
            href = (attrs_dict.get("href") or "").strip()
            if href:
                self.links.append(href)


def opener_for_base() -> tuple[ssl.SSLContext, object]:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    jar = None
    try:
        import http.cookiejar as cookiejar

        jar = cookiejar.CookieJar()
    except Exception:
        jar = None
    # NOTE: urllib openers don't accept a per-request SSL context kwarg.
    # Install an HTTPSHandler with our context so HTTPS requests work.
    op = build_opener(
        HTTPSHandler(context=ctx),
        HTTPCookieProcessor(jar) if jar else HTTPCookieProcessor(),
    )
    return ctx, op


def fetch(ctx: ssl.SSLContext, op, url: str, *, timeout: float = 5.0) -> FetchResult:
    req = Request(url, headers={"User-Agent": "zkprobe"})
    try:
        with op.open(req, timeout=timeout) as resp:
            raw = resp.read()
            status = getattr(resp, "status", 200)
        return FetchResult(url=url, status=int(status), text=raw.decode("utf-8", "replace"))
    except HTTPError as e:
        try:
            raw = e.read() or b""
        except Exception:
            raw = b""
        return FetchResult(url=url, status=int(getattr(e, "code", 0) or 0), text=raw.decode("utf-8", "replace"))


def post_form(ctx: ssl.SSLContext, op, url: str, form: dict[str, str], *, timeout: float = 5.0) -> FetchResult:
    from urllib.parse import urlencode

    data = urlencode(form).encode("utf-8")
    # Try to mimic a browser/XHR call closely.
    origin = url.split("/cgi-bin/")[0]
    req = Request(
        url,
        data=data,
        headers={
            "User-Agent": "zkprobe",
            # Match jQuery override in login.js as closely as possible
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": origin,
            "Referer": origin + "/login.html",
        },
        method="POST",
    )
    try:
        with op.open(req, timeout=timeout) as resp:
            raw = resp.read()
            status = getattr(resp, "status", 200)
        return FetchResult(url=url, status=int(status), text=raw.decode("utf-8", "replace"))
    except HTTPError as e:
        try:
            raw = e.read() or b""
        except Exception:
            raw = b""
        return FetchResult(url=url, status=int(getattr(e, "code", 0) or 0), text=raw.decode("utf-8", "replace"))


def unique(seq: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for s in seq:
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: probe_zkteco_web_after_login.py <base_url>")
        print("Example: probe_zkteco_web_after_login.py https://192.168.1.235/")
        return 2

    base = sys.argv[1].strip()
    if not base.endswith("/"):
        base += "/"

    username = (os.environ.get("ZKACCESS_WEB_USER") or "").strip()
    password = (os.environ.get("ZKACCESS_WEB_PASSWORD") or "").strip()
    if not username or not password:
        print("Missing credentials. Set env ZKACCESS_WEB_USER and ZKACCESS_WEB_PASSWORD.")
        return 3

    ctx, op = opener_for_base()

    login_url = urljoin(base, "cgi-bin/login.cgi")
    # Per login.js: -username is base64, -userpass is md5
    u64 = base64.b64encode(username.encode("utf-8")).decode("ascii")
    md5 = hashlib.md5(password.encode("utf-8")).hexdigest()
    print(f"Login URL: {login_url}")
    print(f"Login user: {username}")

    # AJAX-style POST (matches login.js)
    login_res = post_form(ctx, op, login_url, {"-username": u64, "-userpass": md5})
    head = (login_res.text or "").strip().replace("\r", " ").replace("\n", " ")[:240]
    print(f"Login POST: status={login_res.status} head={head}")

    if not login_res or login_res.status != 200:
        print("Login did not return HTTP 200; cannot continue.")
        return 4

    # Try a few candidate landing pages after login
    candidates = [
        "index.html",
        "main.html",
        "home.html",
        "default.html",
        "frame.html",
        "overview.html",
        "menu.html",
    ]

    pages: list[FetchResult] = []
    for p in candidates:
        url = urljoin(base, p)
        try:
            r = fetch(ctx, op, url, timeout=5.0)
            if r.status == 200 and len((r.text or "").strip()) > 0:
                pages.append(r)
                print(f"Page OK: {p} (len={len(r.text)})")
                # Stop early if it looks like an app shell
                if "<script" in r.text.lower() and "cgi-bin" in r.text.lower():
                    break
        except Exception:
            continue

    if not pages:
        print("No post-login pages fetched successfully; session may not be established.")

    asset_urls: list[str] = []
    for pg in pages:
        parser = AssetParser()
        try:
            parser.feed(pg.text)
        except Exception:
            continue
        for src in parser.scripts:
            asset_urls.append(urljoin(base, src.lstrip("/")))
        for href in parser.links:
            asset_urls.append(urljoin(base, href.lstrip("/")))

    asset_urls = unique([u for u in asset_urls if u.startswith("http")])
    print(f"Assets discovered: {len(asset_urls)}")

    endpoint_re = re.compile(r"/cgi-bin/[^\s'\"]+")
    hits: set[str] = set()

    def scan_text(txt: str) -> None:
        for m in endpoint_re.findall(txt or ""):
            hits.add(m)

    for pg in pages:
        scan_text(pg.text)

    # Fetch and scan a bounded number of assets
    for i, u in enumerate(asset_urls[:40]):
        try:
            r = fetch(ctx, op, u, timeout=5.0)
            if r.status == 200 and r.text:
                scan_text(r.text)
        except Exception:
            continue
        if (i + 1) % 10 == 0:
            print(f"Scanned assets: {i+1}/{min(len(asset_urls),40)}")

    if hits:
        print("\nUnique /cgi-bin endpoints found:")
        for h in sorted(hits):
            print(" ", h)

        # Keyword hints
        keywords = ("comm", "sdk", "port", "server", "encrypt", "key", "adms", "push")
        interesting = [h for h in sorted(hits) if any(k in h.lower() for k in keywords)]
        if interesting:
            print("\nEndpoints containing keywords (comm/sdk/port/server/...):")
            for h in interesting:
                print(" ", h)
    else:
        print("No /cgi-bin endpoints found after login.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
