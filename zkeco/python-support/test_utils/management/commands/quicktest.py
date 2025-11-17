"""
Original code and ideas from http://www.djangosnippets.org/snippets/1318/
Thanks crucialfelix
"""

from django.core.management.base import BaseCommand
import sys


class Command(BaseCommand):
    help = "Runs the test suite, creating a test db IF NEEDED and NOT DESTROYING the test db afterwards. Otherwise operates exactly as does test."

    def add_arguments(self, parser):
        parser.add_argument(
            "test_labels",
            nargs="*",
            help="Optional list of test labels (apps or tests)",
        )
        parser.add_argument(
            "--noinput",
            action="store_false",
            dest="interactive",
            default=True,
            help="Tells Django to NOT prompt the user for input of any kind.",
        )

    def handle(self, *test_labels, **options):
        from django.conf import settings
        from django.test.utils import get_runner

        verbosity = int(options.get("verbosity", 1))
        interactive = options.get("interactive", True)

        settings.TEST_RUNNER = "test_utils.test_runners.keep_database.run_tests"

        test_runner = get_runner(settings)

        failures = test_runner(test_labels, verbosity=verbosity, interactive=interactive)
        if failures:
            sys.exit(failures)
