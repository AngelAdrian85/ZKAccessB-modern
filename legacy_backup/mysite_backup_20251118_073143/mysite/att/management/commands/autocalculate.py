from django.conf import settings

try:
    db_engine = getattr(settings, "DATABASE_ENGINE", None)
    if db_engine == "pool":
        # preserve original behavior when project defines POOL_DATABASE_ENGINE
        settings.DATABASE_ENGINE = getattr(settings, "POOL_DATABASE_ENGINE", db_engine)
except Exception:
    # running under modern settings where these attrs don't exist; ignore
    pass

from django.core.management.base import BaseCommand
import time
import datetime


class Command(BaseCommand):
    help = "Automatic calculate attendance"

    def add_arguments(self, parser):
        # Allow running a single iteration for testing or one-off runs
        parser.add_argument(
            "--once",
            action="store_true",
            dest="once",
            help="Run a single calculation iteration and exit (useful for testing)",
        )

    def handle(self, *args, **options):
        from mysite.iclock.attcalc import auto_calculate  # ,send_msg

        yesterday = datetime.datetime.now().date()
        run_once = options.get("once")
        while True:
            try:
                calculate_all = False
                t_now = datetime.datetime.now()

                if t_now.date() > yesterday and t_now.hour == 2:
                    calculate_all = True
                    yesterday = t_now.date()
                auto_calculate(calculate_all)
                # Sleep only when not running in once mode (avoid delays in tests)
                if run_once:
                    return time.sleep(5)
            except Exception:
                import traceback

                traceback.print_exc()
        # send_msg()
