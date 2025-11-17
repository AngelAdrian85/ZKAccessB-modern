from django.core.management.base import BaseCommand, CommandError
import sys


class Command(BaseCommand):
    help = "Starts a Tornado Web."
    args = '[optional port number, or ipaddr:port]'

    def add_arguments(self, parser):
        parser.add_argument('addrport', nargs='?', default='', help='optional port number, or ipaddr:port')

    def handle(self, addrport='', *args, **options):
        import django
        from django.core.handlers.wsgi import WSGIHandler
        from tornado import httpserver, wsgi, ioloop

        # keep standard streams as-is on Python3

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

        quit_command = 'CTRL-BREAK' if (sys.platform == 'win32') else 'CONTROL-C'

        def inner_run():
            from django.conf import settings
            print("Validating models...")
            self.validate(display_num_errors=True)
            print("\nDjango version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE))
            print("Tornado Server is running at http://%s:%s/" % (addr, port))
            print("Quit the server with %s." % quit_command)
            application = WSGIHandler()
            container = wsgi.WSGIContainer(application)
            http_server = httpserver.HTTPServer(container)
            http_server.listen(int(port), address=addr)
            # use current() for modern tornado versions
            try:
                ioloop.IOLoop.current().start()
            except AttributeError:
                ioloop.IOLoop.instance().start()

        inner_run()

