from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from csv import writer

FORMATS = [
    'address',
    'google',
    'outlook',
    'linkedin',
    'vcard',
]

def full_name(first_name, last_name, username, **extra):
    name = u" ".join(n for n in [first_name, last_name] if n)
    if not name:
        return username
    return name

class Command(BaseCommand):
    help = ("Export user email address list in one of a number of formats.")
    args = "[output file]"
    label = 'filename to save to'

    requires_model_validation = True
    can_import_settings = True
    encoding = 'utf-8'

    def add_arguments(self, parser):
        parser.add_argument('--group', '-g', dest='group', default=None,
                            help='Limit to users which are part of the supplied group name')
        parser.add_argument('--format', '-f', dest='format', default=FORMATS[0], choices=FORMATS,
                            help="output format. May be one of '%s'." % "', '".join(FORMATS))

    def handle(self, *args, **options):
        if len(args) > 1:
            raise CommandError("extra arguments supplied")
        group = options.get('group')
        if group and not Group.objects.filter(name=group).count() == 1:
            names = "', '".join(g['name'] for g in Group.objects.values('name'))
            if names:
                names = "'" + names + "'."
            raise CommandError("Unknown group '%s'. Valid group names are: %s" % (group, names))

        if len(args) and args[0] != '-':
            outfile = open(args[0], 'w', encoding=self.encoding, newline='')
            close_outfile = True
        else:
            outfile = self.stdout
            close_outfile = False

        qs = User.objects.all().order_by('last_name', 'first_name', 'username', 'email')
        if group:
            qs = qs.filter(group__name=group).distinct()
        qs = qs.values('last_name', 'first_name', 'username', 'email')
        try:
            getattr(self, options.get('format'))(qs, outfile)
        finally:
            if close_outfile:
                outfile.close()

    def address(self, qs, out):
        """simple single entry per line in the format of:
            "full name" <my@address.com>;
        """
        out.write("\n".join('"%s" <%s>;' % (full_name(**ent), ent['email']) for ent in qs))
        out.write("\n")

    def google(self, qs, out):
        """CSV format suitable for importing into google GMail
        """
        csvf = writer(out)
        csvf.writerow(['Name', 'Email'])
        for ent in qs:
            csvf.writerow([full_name(**ent), ent['email']])

    def outlook(self, qs, out):
        """CSV format suitable for importing into outlook
        """
        csvf = writer(out)
        columns = ['Name','E-mail Address','Notes','E-mail 2 Address','E-mail 3 Address',
                   'Mobile Phone','Pager','Company','Job Title','Home Phone','Home Phone 2',
                   'Home Fax','Home Address','Business Phone','Business Phone 2',
                   'Business Fax','Business Address','Other Phone','Other Fax','Other Address']
        csvf.writerow(columns)
        empty = [''] * (len(columns) - 2)
        for ent in qs:
            csvf.writerow([full_name(**ent), ent['email']] + empty)

    def linkedin(self, qs, out):
        """CSV format suitable for importing into linkedin Groups.
        perfect for pre-approving members of a linkedin group.
        """
        csvf = writer(out)
        csvf.writerow(['First Name', 'Last Name', 'Email'])
        for ent in qs:
            csvf.writerow([ent['first_name'], ent['last_name'], ent['email']])

    def vcard(self, qs, out):
        try:
            import vobject
        except ImportError:
            raise CommandError("Please install python-vobject to use the vcard export format.")
        for ent in qs:
            card = vobject.vCard()
            card.add('fn').value = full_name(**ent)
            if not ent['last_name'] and not ent['first_name']:
                # fallback to fullname, if both first and lastname are not declared
                card.add('n').value = vobject.vcard.Name(full_name(**ent))
            else:
                card.add('n').value = vobject.vcard.Name(ent['last_name'], ent['first_name'])
            emailpart = card.add('email')
            emailpart.value = ent['email']
            emailpart.type_param = 'INTERNET'
            out.write(card.serialize())
