from django.apps import AppConfig
from pathlib import Path


class IAccessPortConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "iaccess_port"
    verbose_name = "iAccess shim for legacy templates"
    path = str(Path(__file__).resolve().parent)
