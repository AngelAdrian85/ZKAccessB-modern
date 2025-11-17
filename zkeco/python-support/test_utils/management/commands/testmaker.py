import os

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import models

from test_utils.testmaker import Testmaker


class Command(BaseCommand):
    help = "Runs the test server with the testmaker output enabled"

    def add_arguments(self, parser):
        parser.add_argument("addrport", nargs="?", default="", help="server:port to run")
        parser.add_argument("-a", "--app", dest="application", default=None, help="The name of the application to output data to.")
        parser.add_argument("-l", "--logdir", dest="logdirectory", default=os.getcwd(), help="Directory to send tests and fixtures to.")
        parser.add_argument("-x", "--loud", dest="verbosity", default="1", choices=["0", "1", "2"], help="Verbosity level; 0=minimal output, 1=normal output, 2=all output")
        parser.add_argument("-f", "--fixture", dest="fixture", action="store_true", default=False, help="Pass -f to not create a fixture for the data.")
        parser.add_argument("--format", dest="format", default="json", help="Specifies the output serialization format for fixtures.")

    def handle(self, addrport="", *args, **options):
        app = options.get("application")
        verbosity = int(options.get("verbosity", 1))
        create_fixtures = options.get("fixture", False)
        _logdir = options.get("logdirectory")
        fixture_format = options.get("format", "xml")

        if app:
            # get_app is legacy; try models.get_app_label-compatible access if present
            try:
                app = models.get_app(app)
            except Exception:
                # leave app as given (tests will validate)
                pass

        if not app:
            # Don't serialize the whole DB :)
            create_fixtures = False

        testmaker = Testmaker(app, verbosity, create_fixtures, fixture_format, addrport)
        testmaker.prepare(insert_middleware=True)
        try:
            call_command("runserver", addrport=addrport, use_reloader=False)
        except SystemExit:
            if create_fixtures:
                testmaker.make_fixtures()
            else:
                raise
