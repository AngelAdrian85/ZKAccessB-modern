"""
Shim management command that forwards to the real command implemented
under `zkeco_modern.legacy_models.management.commands.import_legacy`.
"""
from importlib import import_module

try:
    mod = import_module('zkeco_modern.legacy_models.management.commands.import_legacy')
    Command = getattr(mod, 'Command')
except Exception:
    # If forwarding fails, provide a fallback command that errors clearly.
    from django.core.management.base import BaseCommand, CommandError


    class Command(BaseCommand):
        help = 'import_legacy command not available (forwarding failed)'

        def handle(self, *args, **options):
            raise CommandError('Forwarding import_legacy failed; ensure zkeco_modern package is importable')
