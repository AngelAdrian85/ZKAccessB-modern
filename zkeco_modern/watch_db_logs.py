import argparse
import os
import sys
import time


def _filter_sys_path() -> None:
    bad_path_markers = ("ZKTeco", "python-support", "Python26")
    sys.path[:] = [
        p
        for p in sys.path
        if not (p and any(marker in p for marker in bad_path_markers))
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Watch DeviceRealtimeLog/DeviceEventLog for new rows in real time."
    )
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--interval", type=float, default=0.2)
    parser.add_argument(
        "--heartbeat",
        type=float,
        default=1.0,
        help="Print a periodic heartbeat (seconds). Set 0 to disable.",
    )
    args = parser.parse_args()

    _filter_sys_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zkeco_config.settings")

    import django  # noqa: PLC0415

    django.setup()

    from django.core.cache import cache  # noqa: PLC0415

    from agent.models import DeviceEventLog, DeviceRealtimeLog  # noqa: PLC0415

    last_r = (
        DeviceRealtimeLog.objects.order_by("-id").values_list("id", flat=True).first()
        or 0
    )
    last_e = (
        DeviceEventLog.objects.order_by("-id").values_list("id", flat=True).first()
        or 0
    )

    print(f"WATCH start last_r={last_r} last_e={last_e}")
    start_ts = time.time()
    deadline = time.time() + float(args.seconds)
    next_beat = time.time() + float(args.heartbeat or 0)

    while time.time() < deadline:
        now = time.time()
        if args.heartbeat and now >= next_beat:
            last_card = cache.get("agent:last_card_read")
            print(
                "...",
                f"t=+{now - start_ts:.1f}s",
                f"last_r={last_r}",
                f"last_e={last_e}",
                f"cache_last_card={last_card}",
            )
            next_beat = now + float(args.heartbeat)

        for r in DeviceRealtimeLog.objects.filter(id__gt=last_r).order_by("id")[:50]:
            raw = (getattr(r, "raw", "") or "").replace("\r", " ").replace("\n", " ")
            raw_short = raw[:200]
            print(
                "RTLOG",
                r.id,
                r.device_id,
                getattr(r, "created_at", None),
                raw_short,
            )
            last_r = r.id

        for e in DeviceEventLog.objects.filter(id__gt=last_e).order_by("id")[:50]:
            ts = getattr(e, "timestamp_str", None)
            print(
                "EVT",
                e.id,
                e.device_id,
                ts,
                getattr(e, "code", "") or "",
                (getattr(e, "raw_line", "") or "").replace("\r", " ").replace("\n", " ")[:200],
            )
            last_e = e.id

        time.sleep(float(args.interval))

    print("WATCH done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
