from django.core.management.base import BaseCommand
from django.db import models
from django.core import management
from django.core.exceptions import ImproperlyConfigured
from south.migration import get_app
from south.hacks import hacks


class Command(BaseCommand):
    help = "Quickly converts the named application to use South if it is currently using syncdb."

    def handle(self, app=None, *args, **options):

        # Make sure we have an app
        if not app:
            self.stdout.write("Please specify an app to convert.")
            return

        # See if the app exists
        app = app.split(".")[-1]
        try:
            app_module = models.get_app(app)
        except ImproperlyConfigured:
            self.stdout.write("There is no enabled application matching '%s'." % app)
            return

        # Try to get its list of models
        model_list = models.get_models(app_module)
        if not model_list:
            self.stdout.write("This application has no models; this command is for applications that already have models syncdb'd.")
            self.stdout.write("Make some models, and then use ./manage.py startmigration %s --initial instead." % app)
            return

        # Ask South if it thinks it's already got migrations
        if get_app(app_module):
            self.stdout.write("This application is already managed by South.")
            return

        # Finally! It seems we've got a candidate, so do the two-command trick
        verbosity = int(options.get('verbosity', 0))
        management.call_command("startmigration", app, initial=True, verbosity=verbosity)

        # Now, we need to re-clean and sanitise appcache
        hacks.clear_app_cache()
        hacks.repopulate_app_cache()

        # Now, migrate
        management.call_command("migrate", app, "0001", fake=True, verbosity=verbosity)

        self.stdout.write("")
        self.stdout.write("App '%s' converted. Note that South assumed the application's models matched the database" % app)
        self.stdout.write("(i.e. you haven't changed it since last syncdb); if you have, you should delete the %s/migrations" % app)
        self.stdout.write("directory, revert models.py so it matches the database, and try again.")
