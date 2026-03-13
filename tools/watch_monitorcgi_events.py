from __future__ import annotations

import argparse
import ssl
import time
from urllib.request import Request, urlopen


def fetch(url: str, timeout: float) -> tuple[int, str]:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = Request(url, headers={"User-Agent": "zkprobe"}, method="GET")
    with urlopen(req, context=ctx, timeout=timeout) as resp:
        body = (resp.read() or b"").decode("utf-8", "replace")
        return int(getattr(resp, "status", 200) or 200), body


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch ZKTeco monitor.cgi and print only event payloads or response changes.")
    parser.add_argument("base_url", help="Example: https://192.168.1.235/cgi-bin/monitor.cgi")
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()

    deadline = time.time() + max(0.5, args.duration)
    baseline = None
    iteration = 0

    while time.time() < deadline:
        iteration += 1
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            status, body = fetch(args.base_url, timeout=args.timeout)
        except Exception as exc:
            print(f"[{ts}] poll={iteration} error={exc}")
            time.sleep(args.interval)
            continue

        if baseline is None:
            baseline = body
            print(f"[{ts}] baseline status={status} len={len(body)} head={body[:160].replace(chr(10), ' | ')}")
        elif body != baseline or 'event' in body.lower() or 'cardno' in body.lower() or 'pin' in body.lower():
            print(f"[{ts}] poll={iteration} status={status} len={len(body)}")
            print(body[:4000].replace('\n', ' | '))
            print("---")
            baseline = body

        time.sleep(args.interval)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
