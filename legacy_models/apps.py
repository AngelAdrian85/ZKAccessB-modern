from django.apps import AppConfig
from pathlib import Path


class LegacyModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'legacy_models'
    verbose_name = 'Legacy Models Shim'
    _repo_root = Path(__file__).resolve().parent.parent
    _modern = _repo_root / 'zkeco_modern' / 'legacy_models'
    path = str(_modern if _modern.exists() else Path(__file__).resolve().parent)
