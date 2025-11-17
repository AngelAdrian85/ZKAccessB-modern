from django.core.management.base import BaseCommand, CommandError
import sys
import smtpd
import asyncore

class Command(BaseCommand):
    help = "Starts a test mail server for development."
    args = '[optional port number or ippaddr:port]'

    requires_model_validation = False

    def handle(self, addrport='', *args, **options):
        if args:
            raise CommandError('Usage is runserver %s' % self.args)
        if not addrport:
            addr = ''
            port = '1025'
        else:
            try:
                addr, port = addrport.split(':')
            except ValueError:
                addr, port = '', addrport
        if not addr:
            addr = '127.0.0.1'

        if not port.isdigit():
            raise CommandError("%r is not a valid port number." % port)
        else:
            port = int(port)

        _quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'

        def inner_run():
            # use self.stdout so Django management handles encoding
            self.stdout.write("Now accepting mail at %s:%s" % (addr, port))
            _server = smtpd.DebuggingServer((addr, port), None)
            asyncore.loop()

        try:
            inner_run()
        except KeyboardInterrupt:
            pass
