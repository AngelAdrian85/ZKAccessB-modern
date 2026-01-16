from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "agent",
            "0016_rename_agent_dstime_name_92f669_idx_agent_dstim_name_b55232_idx_and_more",
        )
    ]

    operations = [
        migrations.CreateModel(
            name="LegacyAreaMeta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("legacy_area_id", models.IntegerField(db_index=True, unique=True)),
                ("code", models.CharField(blank=True, max_length=50, null=True)),
                ("parent_legacy_area_id", models.IntegerField(blank=True, null=True)),
                ("remarks", models.CharField(blank=True, max_length=255, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["legacy_area_id"], name="agent_legacya_legacy__d658d2_idx"),
                    models.Index(fields=["code"], name="agent_legacya_code_5b5452_idx"),
                ],
            },
        ),
    ]
