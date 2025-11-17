from django.core import management
from django.core.management.commands import testserver
from django.conf import settings

from syncdb import Command as SyncDbCommand


class MigrateAndSyncCommand(SyncDbCommand):
    """Compatibility wrapper for older south behavior.

    We avoid manipulating optparse.OptionList here; modern Django tests will
    control migration behavior via settings. This subclass exists as a marker
    and delegates to the upstream SyncDbCommand implementation.
    """
    pass


class Command(testserver.Command):
    def handle(self, *args, **kwargs):
        management.get_commands()
        if (
            not hasattr(settings, "SOUTH_TESTS_MIGRATE")
            or not settings.SOUTH_TESTS_MIGRATE
        ):
            # point at the core syncdb command when creating tests
            # tests should always be up to date with the most recent model structure
            management._commands["syncdb"] = "django.core"
        else:
            management._commands["syncdb"] = MigrateAndSyncCommand()
        super().handle(*args, **kwargs)
