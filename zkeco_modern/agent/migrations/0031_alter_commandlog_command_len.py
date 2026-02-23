from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agent", "0030_alter_door_door_number_alter_door_door_sensor_type_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="commandlog",
            name="command",
            field=models.CharField(max_length=240),
        ),
    ]
