from django.db import migrations


def forwards(apps, schema_editor):
    SystemSettings = apps.get_model('agent', 'SystemSettings')
    Device = apps.get_model('agent', 'Device')

    settings_obj, _ = SystemSettings.objects.get_or_create(
        id=1,
        defaults={'time_zone': 'Etc/GMT+2'},
    )
    tz = (getattr(settings_obj, 'time_zone', '') or 'Etc/GMT+2').strip() or 'Etc/GMT+2'

    # Universal policy: all devices inherit the global system time zone.
    Device.objects.all().update(time_zone=tz)


def backwards(apps, schema_editor):
    # No-op: we don't want to reintroduce mixed data.
    return


class Migration(migrations.Migration):

    dependencies = [
        ('agent', '0024_systemsettings'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
