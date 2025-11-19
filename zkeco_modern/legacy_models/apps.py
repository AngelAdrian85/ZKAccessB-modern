from django.apps import AppConfig


class LegacyModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'legacy_models'
    verbose_name = 'Legacy reconstructed models'
