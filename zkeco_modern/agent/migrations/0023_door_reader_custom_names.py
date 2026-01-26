from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agent", "0022_doorfirstcardrule_doormulticardrule_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="door",
            name="reader_in_custom_name",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="door",
            name="reader_out_custom_name",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
    ]
