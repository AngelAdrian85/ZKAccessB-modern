from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('legacy_models', '0003_add_accesslog'),
    ]
    operations = [
        migrations.AddField(
            model_name='dept',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='legacy_models.dept'),
        ),
        migrations.AddField(
            model_name='employee',
            name='reservation_password',
            field=models.CharField(blank=True, null=True, max_length=64),
        ),
        migrations.AddField(
            model_name='employee',
            name='role_on_device',
            field=models.CharField(blank=True, null=True, max_length=64),
        ),
        migrations.AddField(
            model_name='employee',
            name='elevator_superuser',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='employee',
            name='elevator_level',
            field=models.CharField(blank=True, null=True, max_length=64),
        ),
    ]
