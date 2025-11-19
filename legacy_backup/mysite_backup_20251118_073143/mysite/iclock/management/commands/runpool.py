from django.conf import settings

try:
    db_engine = getattr(settings, "DATABASE_ENGINE", None)
    if db_engine == "pool":
        settings.DATABASE_ENGINE = getattr(settings, "POOL_DATABASE_ENGINE", db_engine)
except Exception:
    pass

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Starts sql pool server."

    def add_arguments(self, parser):
        return

    def handle(self, *args, **options):
        from pool.datapool import runsql

        self.stdout.write(self.help)
        try:
            runsql(settings.POOL_CONNECTION)
        except Exception:
            import traceback

            traceback.print_exc()


