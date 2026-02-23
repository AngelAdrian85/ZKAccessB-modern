from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agent', '0028_systemsettings_ui_prefs'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='subnet_mask',
            field=models.CharField(blank=True, default='', help_text='Subnet mask (e.g., 255.255.255.0)', max_length=32),
        ),
        migrations.AddField(
            model_name='device',
            name='gateway',
            field=models.GenericIPAddressField(blank=True, help_text='Gateway address', null=True),
        ),
    ]
