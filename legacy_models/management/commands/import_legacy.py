"""Compatibility shim for the real `import_legacy` command.

We keep this module at repo root so `legacy_models.management.commands.import_legacy`
exists even when callers run from the repo root (where the `legacy_models/` shim
package shadows `zkeco_modern/legacy_models`).

Important: do NOT import the real command module at import time.
That can run before Django finishes initializing the app registry, leading to
`AppRegistryNotReady` and a degraded fallback that doesn't expose arguments.
"""

from django.core.management.base import BaseCommand, CommandError
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_real_command():
    try:
        repo_root = Path(__file__).resolve().parents[3]
        impl_path = repo_root / 'zkeco_modern' / 'legacy_models' / 'management' / 'commands' / 'import_legacy.py'
        if not impl_path.exists():
            raise FileNotFoundError(str(impl_path))

        spec = spec_from_file_location('_import_legacy_impl', impl_path)
        if spec is None or spec.loader is None:
            raise ImportError(f'Could not load spec for {impl_path}')
        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        real_command_class = getattr(module, 'Command', None)
        if real_command_class is None:
            raise ImportError('Real Command class not found')
        return real_command_class()
    except Exception as exc:
        raise CommandError(
            'Forwarding import_legacy failed; ensure zkeco_modern sources exist'
        ) from exc


class Command(BaseCommand):
    help = "Import legacy CSV exports into Django models."

    def add_arguments(self, parser):
        return _load_real_command().add_arguments(parser)

    def handle(self, *args, **options):
        return _load_real_command().handle(*args, **options)
