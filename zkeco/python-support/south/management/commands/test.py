from django.core import management
from django.core.management.commands import test
from django.conf import settings


class Command(test.Command):
    def add_arguments(self, parser):
        # Reuse django's test command arguments
        super(Command, self).add_arguments(parser)
        # If SOUTH_TESTS_MIGRATE is True, set --migrate default to True
        if getattr(settings, 'SOUTH_TESTS_MIGRATE', False):
            for action in parser._actions:
                if '--migrate' in getattr(action, 'option_strings', []):
                    action.default = True
                    break

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
            # leave management to resolve to the app's syncdb implementation
            management._commands["syncdb"] = management._commands.get("syncdb")
        super(Command, self).handle(*args, **kwargs)
