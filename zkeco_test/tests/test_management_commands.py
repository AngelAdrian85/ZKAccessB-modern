import importlib.util
from pathlib import Path
from django.core.management.base import BaseCommand


def load_module_from_path(mod_name: str, path: str):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(mod)
    return mod


def assert_command_importable_from_path(path: str):
    mod = load_module_from_path('tmp_mod', path)
    assert hasattr(mod, 'Command')
    cmd = getattr(mod, 'Command')
    assert issubclass(cmd, BaseCommand)


def test_mail_debug_command_import():
    p = Path('zkeco') / 'python-support' / 'django_extensions' / 'management' / 'commands' / 'mail_debug.py'
    assert p.exists(), f"Expected {p} to exist"
    assert_command_importable_from_path(str(p))


def test_runserver_plus_command_import():
    p = Path('zkeco') / 'python-support' / 'django_extensions' / 'management' / 'commands' / 'runserver_plus.py'
    assert p.exists(), f"Expected {p} to exist"
    assert_command_importable_from_path(str(p))
