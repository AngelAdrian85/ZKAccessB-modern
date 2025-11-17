# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
import os

# dict4ini is a legacy helper; import if available, otherwise run without persisting ini
try:
    import dict4ini
except Exception:
    dict4ini = None
from django.conf import settings


class Command(BaseCommand):
    help = "test connection"

    def handle(self, *args, **options):
        from django.db import connection as conn

        conn_result = True
        try:
            cur = conn.cursor()
            # Optionally perform a lightweight query to ensure connectivity
            cur.execute("SELECT 1")
            cur.fetchone()
        except Exception as exc:  # pragma: no cover - integration error path
            import traceback

            traceback.print_exc()
            conn_result = "%s" % exc

        # Optionally persist check result to an ini file under APP_HOME if configured
        try:
            app_home = getattr(settings, "APP_HOME", None)
            if app_home:
                test_dict = dict4ini.DictIni(os.path.join(app_home, "test_conn.ini"))
                test_dict["test_result"]["success"] = "%s" % conn_result
                test_dict.save()
        except Exception:
            # best-effort logging only; do not fail the command for ini write issues
            pass
