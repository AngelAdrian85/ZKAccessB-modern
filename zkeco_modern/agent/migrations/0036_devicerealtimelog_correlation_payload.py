from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agent", "0035_wiegandcardformat"),
    ]

    operations = [
        migrations.AddField(
            model_name="devicerealtimelog",
            name="correlation_payload",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]