from __future__ import annotations

from datetime import time

from django.core.management.base import BaseCommand

from agent.models import TimeSegment


class Command(BaseCommand):
    help = "Ensure default TimeSegment rows exist (e.g., ALWAYS 00:00-23:59)."

    def handle(self, *args, **options):
        # "ALWAYS" segment used for quick testing.
        name = "ALWAYS (00:00-23:59)"
        seg, created = TimeSegment.objects.get_or_create(
            name=name,
            defaults={
                "start_time": time(0, 0, 0),
                "end_time": time(23, 59, 59),
                "days_mask": 127,
            },
        )
        if not created:
            # Keep it correct if an older row exists
            changed = False
            if seg.start_time != time(0, 0, 0):
                seg.start_time = time(0, 0, 0)
                changed = True
            if seg.end_time != time(23, 59, 59):
                seg.end_time = time(23, 59, 59)
                changed = True
            if int(seg.days_mask or 0) != 127:
                seg.days_mask = 127
                changed = True
            if changed:
                seg.full_clean()
                seg.save(update_fields=["start_time", "end_time", "days_mask"])

        status = "created" if created else "exists"
        self.stdout.write(f"TimeSegment '{seg.name}' ({seg.start_time}-{seg.end_time}, mask={seg.days_mask}) -> {status}")
