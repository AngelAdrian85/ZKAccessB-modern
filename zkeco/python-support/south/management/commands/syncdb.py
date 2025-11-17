from django.core.management.base import BaseCommand
from django.utils.datastructures import SortedDict
from south import migration
from south.db import db
from django.core.management.commands import syncdb
from django.conf import settings
from django.db import models
from django.db.models.loading import cache
from django.core import management

def get_app_name(app):
    return '.'.join( app.__name__.split('.')[0:-1] )

class Command(BaseCommand):
    help = "Create the database tables for all apps in INSTALLED_APPS whose tables haven't already been created, except those which use migrations."

    def add_arguments(self, parser):
        parser.add_argument('--noinput', action='store_false', dest='interactive', default=True,
                            help='Tells Django to NOT prompt the user for input of any kind.')
        parser.add_argument('--migrate', action='store_true', dest='migrate', default=False,
                            help='Tells South to also perform migrations after the sync. Default for during testing, and other internal calls.')
        parser.add_argument('--all', action='store_true', dest='migrate_all', default=False,
                            help='Makes syncdb work on all apps, even migrated ones. Be careful!')
        parser.add_argument('--verbosity', action='store', dest='verbosity', default='1', choices=['0', '1', '2'],
                            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output')

    def handle(self, *args, **options):
        migrate_all = options.get('migrate_all', False)
        # Work out what uses migrations and so doesn't need syncing
        apps_needing_sync = []
        apps_migrated = []
        for app in models.get_apps():
            app_name = get_app_name(app)
            migrations = migration.get_app(app)
            if migrations is None or migrate_all:
                apps_needing_sync.append(app_name)
            else:
                # This is a migrated app, leave it
                apps_migrated.append(app_name)
        verbosity = int(options.get('verbosity', 0))
        
        # Run syncdb on only the ones needed
        if verbosity:
            print("Syncing...")
        
        old_installed, settings.INSTALLED_APPS = settings.INSTALLED_APPS, apps_needing_sync
        old_app_store, cache.app_store = cache.app_store, SortedDict([
            (k, v) for (k, v) in cache.app_store.items()
            if get_app_name(k) in apps_needing_sync
        ])

        # This will allow the setting of the MySQL storage engine, for example.
        db.connection_init()

        # OK, run the actual syncdb
        syncdb.Command().execute(**options)

        settings.INSTALLED_APPS = old_installed
        cache.app_store = old_app_store

        # Migrate if needed
        if options.get('migrate', True):
            if verbosity:
                print("Migrating...")
            management.call_command('migrate', **options)

        # Be obvious about what we did
        if verbosity:
            print("\nSynced:\n > %s" % "\n > ".join(apps_needing_sync))

        if options.get('migrate', True):
            if verbosity:
                print("\nMigrated:\n - %s" % "\n - ".join(apps_migrated))
        else:
            if verbosity:
                print("\nNot synced (use migrations):\n - %s" % "\n - ".join(apps_migrated))
                print("(use ./manage.py migrate to migrate these)")
