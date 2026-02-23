from __future__ import annotations

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Purge auto-created "(Implicit)" access levels created by provisioning logic.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Actually delete. Without this flag, runs in dry-run mode.',
        )
        parser.add_argument(
            '--pattern',
            default='(Implicit',
            help='Substring to match in AccessLevel.name (default: "(Implicit").',
        )

    def handle(self, *args, **options):
        from agent.models import AccessLevel

        pattern = str(options.get('pattern') or '(Implicit')
        do_delete = bool(options.get('yes'))

        qs = AccessLevel.objects.all()
        if pattern:
            qs = qs.filter(name__contains=pattern)

        items = list(qs.order_by('id'))
        if not items:
            self.stdout.write(self.style.SUCCESS('No implicit access levels found.'))
            return

        self.stdout.write(f'Found {len(items)} access levels matching pattern={pattern!r}:')
        for lvl in items[:200]:
            self.stdout.write(f' - #{lvl.id}: {lvl.name}')
        if len(items) > 200:
            self.stdout.write(f' ... and {len(items) - 200} more')

        if not do_delete:
            self.stdout.write(self.style.WARNING('Dry-run only. Re-run with --yes to delete.'))
            return

        deleted_count, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} rows (including M2M relations).'))
