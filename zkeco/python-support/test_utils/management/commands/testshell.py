from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Runs a development server with data from the given fixture(s)."

    def add_arguments(self, parser):
        parser.add_argument("fixture_labels", nargs="*", help="Fixture labels to load into the test DB")
        parser.add_argument(
            "--addrport",
            action="store",
            dest="addrport",
            default="",
            help="port number or ipaddr:port to run the server on",
        )

    def handle(self, *fixture_labels, **options):
        from django.core.management import call_command
        from django.db import connection
        from django.db.backends import creation
        from django.conf import settings

        verbosity = int(options.get("verbosity", 1))
        _addrport = options.get("addrport")

        # Create a test database.
        connection.creation.create_test_db(verbosity, autoclobber=True)

        if settings.TEST_DATABASE_NAME:
            settings.DATABASE_NAME = settings.TEST_DATABASE_NAME
        else:
            settings.DATABASE_NAME = (
                creation.TEST_DATABASE_PREFIX + settings.DATABASE_NAME
            )

        # Import the fixture data into the test database.
        call_command("loaddata", *fixture_labels, **{"verbosity": verbosity})

        try:
            call_command("shell_plus")
        except Exception:
            # Fall back to plain shell if shell_plus is not available or fails
            call_command("shell")
