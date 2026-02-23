from __future__ import annotations

import hashlib

from django.db import migrations, models


def _compute_signature(ts_id: int, door_ids: list[int]) -> str | None:
    try:
        ts_id_i = int(ts_id or 0)
    except Exception:
        ts_id_i = 0

    try:
        door_ids_i = sorted({int(x) for x in (door_ids or []) if int(x) > 0})
    except Exception:
        door_ids_i = []

    payload = f"ts={ts_id_i};doors={','.join(str(x) for x in door_ids_i)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def backfill_accesslevel_signature(apps, schema_editor):
    AccessLevel = apps.get_model("agent", "AccessLevel")

    # Historical models for M2M tables.
    through_doors = AccessLevel.doors.through
    through_ts = AccessLevel.time_segments.through

    # Track signatures used so we don't violate unique constraints during backfill.
    used: set[str] = set(
        str(s)
        for s in AccessLevel.objects.exclude(signature__isnull=True).values_list("signature", flat=True)
        if s
    )

    for lvl in AccessLevel.objects.all().only("id"):
        lvl_id = int(lvl.id)

        # Pick a single time segment deterministically (lowest id).
        ts_ids = list(
            through_ts.objects.filter(accesslevel_id=lvl_id)
            .values_list("timesegment_id", flat=True)
            .order_by("timesegment_id")
        )
        ts_id = int(ts_ids[0]) if ts_ids else 0

        door_ids = list(
            through_doors.objects.filter(accesslevel_id=lvl_id)
            .values_list("door_id", flat=True)
            .order_by("door_id")
        )

        sig = _compute_signature(ts_id, [int(x) for x in door_ids if x])
        if not sig:
            continue

        if sig in used:
            # Duplicate (tz + door combo) already exists; keep signature NULL so the migration passes.
            # The new form validation will prevent creating/saving duplicates going forward.
            AccessLevel.objects.filter(id=lvl_id).update(signature=None)
            continue

        AccessLevel.objects.filter(id=lvl_id).update(signature=sig)
        used.add(sig)


class Migration(migrations.Migration):

    dependencies = [
        ("agent", "0033_systemsettings_default_comm_password"),
    ]

    operations = [
        migrations.AddField(
            model_name="accesslevel",
            name="is_visitor",
            field=models.BooleanField(default=False, help_text="Nivel vizitatori (Da/Nu)"),
        ),
        migrations.AddField(
            model_name="accesslevel",
            name="signature",
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.RunPython(backfill_accesslevel_signature, migrations.RunPython.noop),
    ]
