from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agent", "0031_alter_commandlog_command_len"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="sync_personnel_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="sync_personnel_dedupe_seconds",
            field=models.PositiveSmallIntegerField(default=60),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="sync_personnel_reassert_seconds",
            field=models.PositiveIntegerField(default=21600),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="sync_personnel_batch_size",
            field=models.PositiveIntegerField(default=200),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="sync_personnel_inter_batch_sleep",
            field=models.FloatField(default=0.02),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="sync_personnel_max_per_minute",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
