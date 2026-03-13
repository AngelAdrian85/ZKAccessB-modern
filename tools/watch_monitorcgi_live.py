from __future__ import annotations

import argparse
import os
import time

from zk_device_web_api import ZkWebTarget, _require_requests, login


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Watch authenticated ZKTeco monitor.cgi responses for live event payloads."
    )
    parser.add_argument("--host", default="192.168.1.235")
    parser.add_argument("--scheme", default="https", choices=["http", "https"])
    parser.add_argument("--port", type=int, default=443)
    parser.add_argument("--duration", type=float, default=120.0)
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()

    username = (os.environ.get("ZKACCESS_WEB_USER") or "").strip()
    password = (os.environ.get("ZKACCESS_WEB_PASSWORD") or "").strip()
    if not username or not password:
        print("ERROR missing ZKACCESS_WEB_USER/ZKACCESS_WEB_PASSWORD", flush=True)
        return 2

    requests = _require_requests()
    session = requests.Session()
    session.verify = False
    try:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except Exception:
        pass

    target = ZkWebTarget(args.scheme, args.host, args.port)
    login_text = login(session, target, username, password, timeout_s=args.timeout)
    print(
        "LOGIN=" + (login_text or "").strip().replace("\r", " ").replace("\n", " ")[:200],
        flush=True,
    )
    print(
        f"WATCH_READY url={target.url('/cgi-bin/monitor.cgi')} duration={args.duration}s interval={args.interval}s",
        flush=True,
    )

    deadline = time.time() + max(1.0, args.duration)
    baseline = None
    poll = 0

    while time.time() < deadline:
        poll += 1
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            resp = session.get(target.url("/cgi-bin/monitor.cgi"), timeout=args.timeout)
            body = resp.text or ""
        except Exception as exc:
            print(f"[{ts}] ERROR poll={poll} {exc}", flush=True)
            try:
                relogin = login(session, target, username, password, timeout_s=args.timeout)
                print(
                    "RELOGIN="
                    + (relogin or "").strip().replace("\r", " ").replace("\n", " ")[:200],
                    flush=True,
                )
            except Exception as relogin_exc:
                print(f"[{ts}] RELOGIN_ERROR {relogin_exc}", flush=True)
            time.sleep(args.interval)
            continue

        interesting = any(
            key in body.lower() for key in ("event", "cardno", "pin", "verifytype")
        )
        if baseline is None:
            baseline = body
            head = body[:220].replace("\n", " | ")
            print(
                f"[{ts}] BASE status={resp.status_code} len={len(body)} head={head}",
                flush=True,
            )
        elif body != baseline or interesting:
            print(
                f"[{ts}] CHANGE poll={poll} status={resp.status_code} len={len(body)} interesting={interesting}",
                flush=True,
            )
            print(body[:4000].replace("\n", " | "), flush=True)
            print("---", flush=True)
            baseline = body

        time.sleep(args.interval)

    print("WATCH_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
