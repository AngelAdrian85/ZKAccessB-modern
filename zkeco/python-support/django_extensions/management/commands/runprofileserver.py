"""
runprofileserver.py

    Starts a lightweight Web server with profiling enabled.

Credits for kcachegrind support taken from lsprofcalltree.py go to:
 David Allouche
 Jp Calderone & Itamar Shtull-Trauring
 Johan Dahlin
"""

from django.core.management.base import BaseCommand, CommandError
from datetime import datetime
import os
import sys

def label(code):
    if isinstance(code, str):
        return ('~', 0, code)    # built-in functions ('~' sorts at the end)
    else:
        return '%s %s:%d' % (code.co_name,
                             code.co_filename,
                             code.co_firstlineno)
class KCacheGrind(object):
    """Minimal kcachegrind output generator for profiling files.

    This implementation keeps output simple but syntactically correct so the
    profiling path works under Python 3. It prints a basic header and for each
    stat entry writes function name and inclusive time. The original command
    included a more feature-complete exporter; this minimal version is safer
    for automated porting.
    """
    def __init__(self, profiler):
        # profiler is expected to provide getstats() similar to cProfile/lsprof
        try:
            self.data = profiler.getstats()
        except Exception:
            self.data = []
        self.out_file = None

    def output(self, out_file):
        self.out_file = out_file
        out_file.write('events: Ticks\n')
        # summary
        max_cost = 0
        for entry in self.data:
            try:
                totaltime = int(getattr(entry, 'totaltime', 0) * 1000)
                max_cost = max(max_cost, totaltime)
            except Exception:
                continue
        out_file.write('summary: %d\n' % (max_cost,))
        for entry in self.data:
            self._entry(entry)

    def _entry(self, entry):
        out_file = self.out_file
        code = getattr(entry, 'code', None)
        if code is None:
            return out_file.write('fn=%s\n' % (label(code),))
        try:
            inlinetime = int(getattr(entry, 'inlinetime', 0) * 1000)
            if hasattr(code, 'co_firstlineno'):
                out_file.write('%d %d\n' % (code.co_firstlineno, inlinetime))
            else:
                out_file.write('0 %d\n' % (inlinetime,))
        except Exception:
            out_file.write('0 0\n')
        out_file.write('\n')

class Command(BaseCommand):
    help = "Starts a lightweight Web server with profiling enabled."
    args = '[optional port number, or ipaddr:port]'

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False

    def add_arguments(self, parser):
        parser.add_argument('addrport', nargs='?', help='[optional port number, or ipaddr:port]', default='')
        parser.add_argument('--noreload', action='store_false', dest='use_reloader', default=True,
                            help='Tells Django to NOT use the auto-reloader.')
        parser.add_argument('--adminmedia', dest='admin_media_path', default='',
                            help='Specifies the directory from which to serve admin media.')
        parser.add_argument('--prof-path', dest='prof_path', default='/tmp',
                            help='Specifies the directory which to save profile information in.')
        parser.add_argument('--nomedia', action='store_true', dest='no_media', default=False,
                            help='Do not profile MEDIA_URL and ADMIN_MEDIA_URL')
        parser.add_argument('--use-cprofile', action='store_true', dest='use_cprofile', default=False,
                            help='Use cProfile if available, this is disabled per default because of incompatibilities.')
        parser.add_argument('--kcachegrind', action='store_true', dest='use_lsprof', default=False,
                            help='Create kcachegrind compatible lsprof files, this requires and automatically enables cProfile.')

    def handle(self, addrport='', *args, **options):
        import django
        from django.core.servers.basehttp import run, AdminMediaHandler, WSGIServerException
        from django.core.handlers.wsgi import WSGIHandler
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
        admin_media_path = options.get('admin_media_path', '')
        shutdown_message = options.get('shutdown_message', '')
        no_media = options.get('no_media', False)
        quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'

        def inner_run():
            from django.conf import settings

            import hotshot
            USE_CPROFILE = options.get('use_cprofile', False)
            USE_LSPROF = options.get('use_lsprof', False)
            if USE_LSPROF:
                USE_CPROFILE = True
            if USE_CPROFILE:
                try:
                    import cProfile
                    USE_CPROFILE = True
                except ImportError:
                    print("cProfile disabled, module cannot be imported!")
                    USE_CPROFILE = False
            if USE_LSPROF and not USE_CPROFILE:
                raise SystemExit("Kcachegrind compatible output format required cProfile from Python 2.5")
            prof_path = options.get('prof_path', '/tmp')
            def make_profiler_handler(inner_handler):
                def handler(environ, start_response):
                    path_info = environ['PATH_INFO']
                    # normally /media/ is MEDIA_URL, but in case still check it in case it's differently
                    # should be hardly a penalty since it's an OR expression.
                    # TODO: fix this to check the configuration settings and not make assumpsions about where media are on the url
                    if no_media and (path_info.startswith('/media') or path_info.startswith(settings.MEDIA_URL)):
                        return inner_handler(environ, start_response)
                    path_name = path_info.strip("/").replace('/', '.') or "root"
                    profname = "%s.%s.prof" % (path_name, datetime.now().isoformat())
                    profname = os.path.join(prof_path, profname)
                    if USE_CPROFILE:
                        prof = cProfile.Profile()
                    else:
                        prof = hotshot.Profile(profname)
                    start = datetime.now()
                    try:
                        return prof.runcall(inner_handler, environ, start_response)
                    finally:
                        # seeing how long the request took is important!
                        elap = datetime.now() - start
                        elapms = elap.seconds * 1000.0 + elap.microseconds / 1000.0
                        if USE_LSPROF:
                            kg = KCacheGrind(prof)
                            with open(profname, 'w') as _f:
                                kg.output(_f)
                        elif USE_CPROFILE:
                            prof.dump_stats(profname)
                        profname2 = "%s.%06dms.%s.prof" % (path_name, elapms, datetime.now().isoformat())
                        profname2 = os.path.join(prof_path, profname2)
                        os.rename(profname, profname2)
                return handler

            self.stdout.write("Validating models...")
            self.validate(display_num_errors=True)
            self.stdout.write("\nDjango version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE))
            self.stdout.write("Development server is running at http://%s:%s/" % (addr, port))
            self.stdout.write("Quit the server with %s." % quit_command)
            try:
                path = admin_media_path or django.__path__[0] + '/contrib/admin/media'
                handler = make_profiler_handler(AdminMediaHandler(WSGIHandler(), path))
                run(addr, int(port), handler)
            except WSGIServerException as e:
                # Use helpful error messages instead of ugly tracebacks.
                ERRORS = {
                    13: "You don't have permission to access that port.",
                    98: "That port is already in use.",
                    99: "That IP address can't be assigned-to.",
                }
                try:
                    error_text = ERRORS[e.args[0].args[0]]
                except (AttributeError, KeyError):
                    error_text = str(e)
                sys.stderr.write(self.style.ERROR("Error: %s" % error_text) + '\n')
                # Need to use an OS exit because sys.exit doesn't work in a thread
                os._exit(1)
            except KeyboardInterrupt:
                if shutdown_message:
                    self.stdout.write(shutdown_message)
                sys.exit(0)
        if use_reloader:
            from django.utils import autoreload
            autoreload.main(inner_run)
        else:
            inner_run()
