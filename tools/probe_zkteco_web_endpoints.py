"""Probe ZKTeco Webserver assets for CGI endpoints.

This is a diagnostics helper. It does NOT perform login.
"""

from __future__ import annotations

import re
import ssl
import sys
from urllib.parse import urljoin
from urllib.request import Request, urlopen


def fetch_text(url: str, *, timeout: float = 4.0) -> str:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = Request(url, headers={"User-Agent": "zkprobe"})
    with urlopen(req, context=ctx, timeout=timeout) as resp:
        raw = resp.read()
    return raw.decode("utf-8", "replace")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: probe_zkteco_web_endpoints.py <base_url>")
        print("Example: probe_zkteco_web_endpoints.py https://192.168.1.235/")
        return 2

    base = sys.argv[1].strip()
    if not base.endswith("/"):
        base += "/"

    paths = [
        "login.html",
        "js/login.js",
        "js/common.js",
        "js/login.js",
        "js/jquery.alerts.js",
        "js/jquery_dialog.js",
    ]

    endpoint_re = re.compile(r"/cgi-bin/[^\s'\"]+")

    all_hits: set[str] = set()
    for p in paths:
        url = urljoin(base, p)
        try:
            s = fetch_text(url)
        except Exception as e:
            print(f"FAIL {p}: {e}")
            continue

        hits = sorted(set(endpoint_re.findall(s)))
        if hits:
            print(f"{p}: {len(hits)} cgi refs")
            for h in hits:
                all_hits.add(h)

    if all_hits:
        print("\nUnique /cgi-bin endpoints:")
        for h in sorted(all_hits):
            print(" ", h)
    else:
        print("No /cgi-bin endpoints found in fetched assets.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
