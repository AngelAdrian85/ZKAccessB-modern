from __future__ import annotations

from typing import Optional

from django.db import transaction

from .models import AccessLevel, Device, Door, TimeSegment


def ensure_default_access_level_for_device(device: Device) -> Optional[AccessLevel]:
    """Ensure a newly-added controller has at least one AccessLevel that references its doors.

    Why:
    - The "Niveluri acces" UI shows doors only when they are assigned to a level.
    - CommCenter sync requires at least one AccessLevel for a device (see `no_access_levels_for_device`).

    Behavior:
    - Only for controller devices.
    - If any AccessLevel already references any door on this device, do nothing.
    - Otherwise, create one default level, attach all doors for this device.
    - Attach the first TimeSegment if available (best-effort), to make sync defaults sane.
    """

    try:
        if not device or not getattr(device, "pk", None):
            return None
    except Exception:
        return None

    try:
        if not device.is_controller():
            return None
    except Exception:
        return None

    device_id = int(device.pk)

    # Doors must exist to create a meaningful level.
    doors_qs = Door.objects.filter(device_id=device_id).exclude(door_number__isnull=True)
    if not doors_qs.exists():
        return None

    # If any access level already covers this device, keep hands off.
    if AccessLevel.objects.filter(doors__device_id=device_id).distinct().exists():
        return None

    def _mk_name() -> str:
        base = (getattr(device, "name", "") or "").strip() or f"Centrala {device_id}"
        # Keep space for suffix, AccessLevel.name max_length is 64.
        base = base[:48].strip()

        cand = f"{base} (Implicit)"[:64]
        if not AccessLevel.objects.filter(name=cand).exists():
            return cand

        cand = f"{base} (Implicit {device_id})"[:64]
        if not AccessLevel.objects.filter(name=cand).exists():
            return cand

        # Very unlikely; last-resort counter.
        for i in range(2, 50):
            cand = f"{base} (Implicit {device_id}-{i})"[:64]
            if not AccessLevel.objects.filter(name=cand).exists():
                return cand

        return f"Centrala {device_id} (Implicit)"[:64]

    with transaction.atomic():
        # Re-check under lock-ish semantics.
        if AccessLevel.objects.filter(doors__device_id=device_id).distinct().exists():
            return None

        level = AccessLevel.objects.create(name=_mk_name(), description="")
        level.doors.add(*list(doors_qs))

        try:
            seg0 = TimeSegment.objects.order_by("id").first()
            if seg0 is not None:
                level.time_segments.add(seg0)
        except Exception:
            pass

        return level
