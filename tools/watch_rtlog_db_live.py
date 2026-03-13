from __future__ import annotations

import argparse
import os
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch DeviceRealtimeLog rows for a device.")
    parser.add_argument("--device-id", type=int, default=22)
    parser.add_argument("--duration", type=float, default=180.0)
    parser.add_argument("--interval", type=float, default=0.5)
    args = parser.parse_args()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zkeco_config.settings")

    import django

    django.setup()

    from agent.models import DeviceRealtimeLog

    last = (
        DeviceRealtimeLog.objects.filter(device_id=args.device_id)
        .order_by("-id")
        .values("id")
        .first()
    )
    last_id = int(last["id"]) if last else 0
    print(f"WATCH_READY device_id={args.device_id} last_id={last_id}", flush=True)

    deadline = time.time() + max(1.0, args.duration)
    while time.time() < deadline:
        rows = list(
            DeviceRealtimeLog.objects.filter(device_id=args.device_id, id__gt=last_id)
            .order_by("id")
            .values("id", "created_at", "sn", "raw")[:50]
        )
        for row in rows:
            last_id = max(last_id, int(row["id"]))
            created = row["created_at"].isoformat() if row.get("created_at") else ""
            raw = str(row.get("raw") or "").replace("\r", " ").replace("\n", " | ")
            print(
                f"ROW id={row['id']} created_at={created} sn={row.get('sn') or ''} raw={raw[:1200]}",
                flush=True,
            )
        time.sleep(args.interval)

    print("WATCH_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
