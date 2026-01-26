from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agent", "0027_timezone_setting_region"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="date_format",
            field=models.CharField(blank=True, default="ro_short", max_length=16),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="week_start",
            field=models.CharField(blank=True, default="monday", max_length=8),
        ),
    ]
