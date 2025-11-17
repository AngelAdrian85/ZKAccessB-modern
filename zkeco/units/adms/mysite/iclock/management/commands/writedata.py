# -*- coding: utf-8 -*-
from django.conf import settings

try:
    db_engine = getattr(settings, "DATABASE_ENGINE", None)
    if db_engine == "pool":
        settings.DATABASE_ENGINE = getattr(settings, "POOL_DATABASE_ENGINE", db_engine)
except Exception:
    pass

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Starts write data process."

    def add_arguments(self, parser):
        return

    def handle(self, *args, **options):
        from mysite.iclock.models.model_cmmdata import process_writedata
        from django.db import connection as conn

        while True:
            process_writedata()
            try:
                cur = conn.cursor()
                cur.close()
                conn.close()
            except Exception:
                pass
