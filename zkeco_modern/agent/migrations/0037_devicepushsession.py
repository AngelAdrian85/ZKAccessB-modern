from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("agent", "0036_devicerealtimelog_correlation_payload"),
    ]

    operations = [
        migrations.CreateModel(
            name="DevicePushSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("serial_number", models.CharField(blank=True, default="", max_length=64)),
                ("remote_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("session_id", models.CharField(max_length=64, unique=True)),
                ("registry_code", models.CharField(blank=True, default="", max_length=64)),
                ("protocol_version_seen", models.CharField(blank=True, default="", max_length=32)),
                ("supports_encrypt", models.BooleanField(default=False)),
                ("supports_https", models.BooleanField(default=False)),
                ("requested_tables", models.CharField(blank=True, default="", max_length=255)),
                ("last_registry_at", models.DateTimeField(blank=True, null=True)),
                ("last_poll_at", models.DateTimeField(blank=True, null=True)),
                ("last_cdata_at", models.DateTimeField(blank=True, null=True)),
                ("last_querydata_at", models.DateTimeField(blank=True, null=True)),
                ("last_control_at", models.DateTimeField(blank=True, null=True)),
                ("last_file_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("session_meta", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("device", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="agent.device")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["device", "updated_at"], name="agent_devic_device__82c8a7_idx"),
                    models.Index(fields=["serial_number", "updated_at"], name="agent_devic_serial__9e1b24_idx"),
                    models.Index(fields=["remote_ip", "updated_at"], name="agent_devic_remote__2ddae6_idx"),
                    models.Index(fields=["expires_at"], name="agent_devic_expires_27dca8_idx"),
                ],
            },
        ),
    ]