import os
from django.core.management.base import BaseCommand
from django.db.backends import util

from debug_toolbar.utils import sqlparse

class PrintQueryWrapper(util.CursorDebugWrapper):
    def execute(self, sql, params=()):
        try:
            return self.cursor.execute(sql, params)
        finally:
            raw_sql = self.db.ops.last_executed_query(self.cursor, sql, params)
            print(sqlparse.format(raw_sql, reindent=True))
            print()

util.CursorDebugWrapper = PrintQueryWrapper

# The rest is copy/paste from django/core/management/commands/shell.py

class Command(BaseCommand):
    help = "Runs a Python interactive interpreter. Tries to use IPython, if it's available."

    requires_model_validation = False

    def add_arguments(self, parser):
        parser.add_argument('--plain', action='store_true', dest='plain', help='Tells Django to use plain Python, not IPython.')

    def handle(self, *args, **options):
        # XXX: (Temporary) workaround for ticket #1796: force early loading of all
        # models from installed apps.
        from django.db.models.loading import get_models
        _loaded_models = get_models()
        use_plain = options.get('plain', False)

        try:
            if use_plain:
                # Don't bother loading IPython, because the user wants plain Python.
                raise ImportError
            import IPython
            # IPython API changed over versions; try a compatible invocation
            try:
                shell = IPython.terminal.embed.InteractiveShellEmbed()
                shell()
            except Exception:
                # Fallback to older API
                try:
                    shell = IPython.Shell.IPShell(argv=[])
                    shell.mainloop()
                except Exception:
                    raise
        except Exception:
            import code
            # Set up a dictionary to serve as the environment for the shell, so
            # that tab completion works on objects that are imported at runtime.
            imported_objects = {}
            try: # Try activating rlcompleter, because it's handy.
                import readline
            except ImportError:
                pass
            else:
                # We don't have to wrap the following import in a 'try', because
                # we already know 'readline' was imported successfully.
                import rlcompleter
                readline.set_completer(rlcompleter.Completer(imported_objects).complete)
                try:
                    readline.parse_and_bind("tab:complete")
                except Exception:
                    # Some platforms use different bind syntax; ignore failures
                    pass

            # We want to honor both $PYTHONSTARTUP and .pythonrc.py, so follow system
            # conventions and get $PYTHONSTARTUP first then import user.
            if not use_plain:
                pythonrc = os.environ.get("PYTHONSTARTUP")
                if pythonrc and os.path.isfile(pythonrc):
                    try:
                        exec(open(pythonrc, 'r').read(), {})
                    except Exception:
                        pass
                # This will import .pythonrc.py as a side-effect if present
                try:
                    pass
                except Exception:
                    # user module may not exist on all platforms
                    pass
            code.interact(local=imported_objects)
