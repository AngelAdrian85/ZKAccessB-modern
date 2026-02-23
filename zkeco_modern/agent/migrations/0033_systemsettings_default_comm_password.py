from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agent", "0032_systemsettings_sync_personnel_limits"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="default_comm_password",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
