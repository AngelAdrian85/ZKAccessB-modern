from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import re

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

    location = (getattr(device, "area_name", "") or "").strip()

    def _looks_auto_provisioned_name(name: str, door_no: int) -> bool:
        nm = (name or "").strip()
        if not nm:
            return False
        if not nm.endswith(f" {door_no}"):
            return False
        prefix = nm[: -(len(str(door_no)) + 1)].strip()
        if not prefix:
            return False
        up = prefix.upper()
        if up.startswith("DEVICE"):
            return True
        if up in ("CENTRALĂ", "CENTRALA", "CONTROLLER"):
            return True
        try:
            ipaddress.ip_address(prefix)
            return True
        except Exception:
            pass
        return bool(re.fullmatch(r"[A-Z0-9._-]{3,}", prefix)) and (" " not in prefix)

    with transaction.atomic():
        for door_no in range(1, capacity + 1):
            expected_name = f"Ușă {door_no}"  # neutral, never looks like a controller

            # If there is already a door with this index, keep it (but rename old auto-names).
            d = Door.objects.filter(device=device, door_number=door_no).first()
            if d is None:
                # Prefer to take an existing unnumbered door already linked to this controller.
                candidate = (
                    Door.objects.filter(device=device, door_number__isnull=True)
                    .order_by("id")
                    .first()
                )
                if candidate is not None:
                    candidate.door_number = door_no
                    candidate.save(update_fields=["door_number"])
                    d = candidate
                    existing += 1
                else:
                    d = Door.objects.create(
                        device=device,
                        door_number=door_no,
                        name=expected_name,
                        location=location,
                        enabled=True,
                        normally_open=True,
                    )
                    created += 1
            else:
                existing += 1

            # Auto-rename only if it looks auto-provisioned (avoid overwriting user names).
            if expected_name and (d.name or "").strip() != expected_name:
                if _looks_auto_provisioned_name(d.name or "", door_no):
                    d.name = expected_name
                    d.save(update_fields=["name"])

            # Keep derived defaults reasonably in sync for auto-created doors.
            # If user customized location we do not overwrite.
            if (not (d.location or "").strip()) and location:
                d.location = location
                d.save(update_fields=["location"])

    return DoorProvisionResult(capacity=capacity, created=created, existing=existing)
