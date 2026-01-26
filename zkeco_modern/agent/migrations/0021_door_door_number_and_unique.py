from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("agent", "0020_employeecard_agent_emplo_slot_afcac6_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="door",
            name="door_number",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4")],
                help_text="Door index on controller (1-4)",
            ),
        ),
        migrations.AddIndex(
            model_name="door",
            index=models.Index(fields=["device", "door_number"], name="agent_door_device__c34d09_idx"),
        ),
        migrations.AddConstraint(
            model_name="door",
            constraint=models.UniqueConstraint(
                fields=("device", "door_number"),
                condition=Q(("door_number__isnull", False)),
                name="uniq_door_per_device_number",
            ),
        ),
    ]
