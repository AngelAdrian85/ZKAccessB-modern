from django.core.management.base import BaseCommand, CommandError
import sys

def null_technical_500_response(request, exc_type, exc_value, tb):
    # Re-raise the original exception with its traceback on Python 3
    try:
        raise exc_value.with_traceback(tb)
    except AttributeError:
        # Fallback: raise a new exception instance of the same type
        raise exc_type(exc_value).with_traceback(tb)

class Command(BaseCommand):
    help = "Starts a lightweight Web server for development."

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False

    def add_arguments(self, parser):
        parser.add_argument('addrport', nargs='?', help='[optional port number, or ipaddr:port]', default='')
        parser.add_argument('--noreload', action='store_false', dest='use_reloader', default=True,
                            help='Tells Django to NOT use the auto-reloader.')
        parser.add_argument('--browser', action='store_true', dest='open_browser',
                            help='Tells Django to open a browser.')
        parser.add_argument('--adminmedia', dest='admin_media_path', default='',
                            help='Specifies the directory from which to serve admin media.')

    def handle(self, addrport='', *args, **options):
        import django
        from django.core.servers.basehttp import AdminMediaHandler
        from django.core.handlers.wsgi import WSGIHandler
        try:
            from werkzeug import run_simple, DebuggedApplication
        except Exception:
            raise CommandError("Werkzeug is required to use runserver_plus.  Please visit http://werkzeug.pocoo.org/download")

        # usurp django's handler
        from django.views import debug
        debug.technical_500_response = null_technical_500_response

        if args:
            raise CommandError('Usage is runserver %s' % self.args)
        if not addrport:
            addr = ''
            port = '8000'
        else:
            try:
                addr, port = addrport.split(':')
            except ValueError:
                addr, port = '', addrport
        if not addr:
            addr = '127.0.0.1'

        if not port.isdigit():
            raise CommandError("%r is not a valid port number." % port)

        use_reloader = options.get('use_reloader', True)
        open_browser = options.get('open_browser', False)
        admin_media_path = options.get('admin_media_path', '')
        _shutdown_message = options.get('shutdown_message', '')
        _quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'

        def inner_run():
            from django.conf import settings
            print("Validating models...")
            self.validate(display_num_errors=True)
            print("\nDjango version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE))
            print("Development server is running at http://%s:%s/" % (addr, port))
            print("Using the Werkzeug debugger (http://werkzeug.pocoo.org/)")
            print("Quit the server with %s." % _quit_command)
            path = admin_media_path or django.__path__[0] + '/contrib/admin/media'
            handler = AdminMediaHandler(WSGIHandler(), path)
            if open_browser:
                import webbrowser
                url = "http://%s:%s/" % (addr, port)
                webbrowser.open(url)
            run_simple(addr, int(port), DebuggedApplication(handler, True), 
                       use_reloader=use_reloader, use_debugger=True)            
        inner_run()
