from django.apps import AppConfig
from pathlib import Path


class LegacyModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'legacy_models'
    verbose_name = 'Legacy reconstructed models'
    path = str(Path(__file__).resolve().parent)
