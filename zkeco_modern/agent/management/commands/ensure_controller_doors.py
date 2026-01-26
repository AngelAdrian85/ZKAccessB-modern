from __future__ import annotations

from django.core.management.base import BaseCommand

from agent.door_provisioning import ensure_controller_doors
from agent.models import Device


class Command(BaseCommand):
    help = "Ensure controller devices have Door rows 1..N (derived from model/type)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--device-id",
            type=int,
            default=None,
            help="If provided, only provision doors for this Device.id",
        )

    def handle(self, *args, **options):
        device_id = options.get("device_id")

        qs = Device.objects.all().order_by("id")
        if device_id:
            qs = qs.filter(id=device_id)

        total_devices = 0
        total_created = 0
        for dev in qs:
            try:
                if not dev.is_controller():
                    continue
            except Exception:
                continue
            total_devices += 1
            res = ensure_controller_doors(dev)
            total_created += res.created
            self.stdout.write(
                f"Device {dev.id} {dev.name} ip={dev.ip_address} type={dev.device_type} -> capacity={res.capacity} created={res.created}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Controllers processed={total_devices} doors_created={total_created}"
            )
        )
