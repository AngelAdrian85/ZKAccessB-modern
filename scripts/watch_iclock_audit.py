import argparse
import os
import sys
import time


def _filter_bad_syspath() -> None:
    # Legacy vendor installs can inject Python 2.6 paths with incompatible .pyc
    bad_path_markers = ("ZKTeco", "python-support", "Python26")
    sys.path[:] = [
        p
        for p in sys.path
        if not (p and any(marker in p for marker in bad_path_markers))
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch agent.AuditLog for iclock traffic")
    parser.add_argument("--seconds", type=int, default=300)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--prefix", type=str, default="iclock")
    args = parser.parse_args()

    _filter_bad_syspath()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zkeco_config.settings")

    print(f"watch_iclock_audit starting seconds={args.seconds} interval={args.interval}")

    import django  # noqa: E402

    django.setup()

    # Use a monotonic clock for loop control. System time can jump (NTP), which
    # would make time.time()-based loops exit early.
    start_mono = time.monotonic()

    from agent.models import AuditLog  # noqa: E402

    last_id = (
        AuditLog.objects.filter(module__startswith=args.prefix)
        .order_by("-id")
        .values_list("id", flat=True)
        .first()
        or 0
    )
    print(f"watch_iclock_audit start prefix={args.prefix!r} last_id={last_id}")

    end_mono = start_mono + float(args.seconds)
    while time.monotonic() < end_mono:
        rows = list(
            AuditLog.objects.filter(module__startswith=args.prefix, id__gt=last_id)
            .order_by("id")[:50]
        )
        for a in rows:
            # Keep it compact + greppable
            print(f"AUD {a.id} {a.timestamp} {a.module} {a.remote_ip} {a.message}")
            last_id = a.id
        time.sleep(float(args.interval))

    print("watch_iclock_audit done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
