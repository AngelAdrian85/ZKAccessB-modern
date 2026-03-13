from __future__ import annotations

import argparse
import os
import sys
import time

import django


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch DeviceRealtimeLog rows for a specific device.")
    parser.add_argument("--device-id", type=int, required=True)
    parser.add_argument("--duration", type=float, default=45.0)
    parser.add_argument("--interval", type=float, default=0.5)
    args = parser.parse_args()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zkeco_config.settings")
    django.setup()

    from agent.models import DeviceRealtimeLog

    seen = DeviceRealtimeLog.objects.order_by("-id").first()
    last_id = int(seen.id) if seen else 0
    print(f"START last_id={last_id} device_id={args.device_id}")
    sys.stdout.flush()

    deadline = time.time() + max(1.0, args.duration)
    while time.time() < deadline:
        rows = list(
            DeviceRealtimeLog.objects.filter(id__gt=last_id, device_id=args.device_id)
            .order_by("id")[:20]
        )
        for row in rows:
            print(
                f"RTLOG id={row.id} created_at={row.created_at.isoformat()} raw={row.raw!r}"
            )
            last_id = int(row.id)
        sys.stdout.flush()
        time.sleep(max(0.1, args.interval))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
