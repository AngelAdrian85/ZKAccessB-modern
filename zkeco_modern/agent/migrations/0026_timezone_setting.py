from django.db import migrations, models


def forwards(apps, schema_editor):
    SystemSettings = apps.get_model('agent', 'SystemSettings')
    TimeZoneSetting = apps.get_model('agent', 'TimeZoneSetting')

    settings_obj, _ = SystemSettings.objects.get_or_create(
        id=1,
        defaults={'time_zone': 'Etc/GMT+2'},
    )
    tz = (getattr(settings_obj, 'time_zone', '') or 'Etc/GMT+2').strip() or 'Etc/GMT+2'

    # Create a default preset if none exist
    if not TimeZoneSetting.objects.exists():
        TimeZoneSetting.objects.create(
            name='Default',
            time_zone=tz,
            is_active=True,
        )
    else:
        # Ensure at least one active preset exists.
        if not TimeZoneSetting.objects.filter(is_active=True).exists():
            first = TimeZoneSetting.objects.order_by('id').first()
            if first is not None:
                TimeZoneSetting.objects.filter(id=first.id).update(is_active=True)


def backwards(apps, schema_editor):
    # Keep data; no-op.
    return


class Migration(migrations.Migration):

    dependencies = [
        ('agent', '0025_normalize_device_time_zone'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeZoneSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('time_zone', models.CharField(max_length=64)),
                ('is_active', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['is_active'], name='tzs_active_idx'),
                    models.Index(fields=['time_zone'], name='tzs_tz_idx'),
                ],
            },
        ),
        migrations.RunPython(forwards, backwards),
    ]
