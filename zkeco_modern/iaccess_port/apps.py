from django.apps import AppConfig


class IAccessPortConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "iaccess_port"
    verbose_name = "iAccess shim for legacy templates"
