from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agent", "0023_door_reader_custom_names"),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemSettings",
            fields=[
                ("id", models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ("time_zone", models.CharField(blank=True, default="Etc/GMT+2", max_length=64)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
