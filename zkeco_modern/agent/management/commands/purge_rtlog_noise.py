from __future__ import annotations

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Delete known noisy RTLog rows (card=0, door=0, code=200) to prevent false AccessLog entries."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually delete rows. Without this flag, runs in dry-run mode.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Optional max rows to delete (0 = no limit).",
        )

    def handle(self, *args, **options):
        apply = bool(options.get("apply"))
        limit = int(options.get("limit") or 0)

        from agent.models import DeviceRealtimeLog

        qs = DeviceRealtimeLog.objects.filter(raw__contains=",0,0,200,0,0").order_by("id")
        total = qs.count()

        self.stdout.write(f"Matched noisy RTLog rows: {total}")

        sample = list(qs.values_list("id", "raw")[:5])
        if sample:
            self.stdout.write("Sample:")
            for rid, raw in sample:
                self.stdout.write(f"  id={rid} raw={raw}")

        if not apply:
            self.stdout.write("Dry-run only. Re-run with --apply to delete.")
            return

        if limit > 0:
            ids = list(qs.values_list("id", flat=True)[:limit])
            deleted, _ = DeviceRealtimeLog.objects.filter(id__in=ids).delete()
            self.stdout.write(f"Deleted rows (limited): {deleted}")
        else:
            deleted, _ = qs.delete()
            self.stdout.write(f"Deleted rows: {deleted}")
