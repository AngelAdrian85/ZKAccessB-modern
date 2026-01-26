from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agent", "0026_timezone_setting"),
    ]

    operations = [
        migrations.AddField(
            model_name="timezonesetting",
            name="region",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
