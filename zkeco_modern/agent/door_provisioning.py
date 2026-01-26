from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from .models import Device, Door


@dataclass(frozen=True)
class DoorProvisionResult:
    capacity: int
    created: int
    existing: int


def infer_controller_door_capacity(device: Device) -> int:
    """Infer controller door count.

    Priority:
    1) Parse known model strings from hardware/firmware/name (ACP-100/200/400, C3-100/200/400)
    2) Fall back to explicit device_type (two_door_panel/multi_door_panel)
    3) Conservative default: 1 door
    """
    try:
        if not device.is_controller():
            return 0
    except Exception:
        return 0

    haystack = " ".join(
        [
            (getattr(device, "hardware_version", "") or ""),
            (getattr(device, "firmware_version", "") or ""),
            (getattr(device, "name", "") or ""),
        ]
    ).upper()

    # Common ZKTeco access panels
    if any(tok in haystack for tok in ("ACP-400", "C3-400", "INBIO-460", "4-DOOR", "4 DOOR")):
        return 4
    if any(tok in haystack for tok in ("ACP-300", "C3-300", "INBIO-360", "3-DOOR", "3 DOOR")):
        return 3
    if any(tok in haystack for tok in ("ACP-200", "C3-200", "INBIO-260", "2-DOOR", "2 DOOR")):
        return 2
    if any(tok in haystack for tok in ("ACP-100", "C3-100", "INBIO-160", "1-DOOR", "1 DOOR")):
        return 1

    dt = (getattr(device, "device_type", "") or "").lower()
    if dt == "two_door_panel":
        return 2
    if dt == "multi_door_panel":
        return 4

    # Default for generic access_panel/door_controller
    return 1


def ensure_controller_doors(device: Device) -> DoorProvisionResult:
    """Create missing Door rows for a controller.

    Creates (device, door_number) for door_number in 1..capacity.
    Does NOT delete/disable any extra doors if capacity changes.
    """
    capacity = infer_controller_door_capacity(device)
    if capacity <= 0:
        return DoorProvisionResult(capacity=0, created=0, existing=0)

    created = 0
    existing = 0

    base_name = (getattr(device, "name", "") or "").strip()
    ip = getattr(device, "ip_address", None)
    for_defaults_prefix = base_name or (str(ip) if ip else "Centrală")
    location = (getattr(device, "area_name", "") or "").strip()

    with transaction.atomic():
        for door_no in range(1, capacity + 1):
            d, was_created = Door.objects.get_or_create(
                device=device,
                door_number=door_no,
                defaults={
                    "name": f"{for_defaults_prefix} {door_no}".strip(),
                    "location": location,
                    "enabled": True,
                },
            )
            if was_created:
                created += 1
            else:
                existing += 1
                # Keep derived defaults reasonably in sync for auto-created doors.
                # If user customized name/location we do not overwrite.
                if (not (d.location or "").strip()) and location:
                    d.location = location
                    d.save(update_fields=["location"])

    return DoorProvisionResult(capacity=capacity, created=created, existing=existing)
