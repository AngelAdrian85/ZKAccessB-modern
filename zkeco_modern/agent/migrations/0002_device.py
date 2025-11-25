from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('agent', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('device_type', models.CharField(default='Access Control Panel', max_length=64)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('area_name', models.CharField(blank=True, default='', max_length=64)),
                ('enabled', models.BooleanField(default=True)),
                ('serial_number', models.CharField(blank=True, default='', max_length=64)),
                ('firmware_version', models.CharField(blank=True, default='', max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={},
        ),
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['serial_number'], name='agent_devic_serial__idx'),
        ),
        migrations.AddIndex(
            model_name='device',
            index=models.Index(fields=['ip_address'], name='agent_devic_ip_addre_idx'),
        ),
    ]
