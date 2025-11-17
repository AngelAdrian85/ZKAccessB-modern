import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock



def test_test_conn_runs(monkeypatch):
    # Load the command module by file path to avoid package import issues
    repo_root = Path(__file__).resolve().parents[2]
    cmd_path = repo_root / "zkeco" / "units" / "adms" / "mysite" / "worktable" / "management" / "commands" / "test_conn.py"
    spec = importlib.util.spec_from_file_location("worktable.test_conn_local", str(cmd_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    # Mock the Django DB connection cursor so we don't require a real DB
    fake_conn = MagicMock()
    fake_cursor = MagicMock()
    fake_cursor.fetchone.return_value = (1,)
    fake_conn.cursor.return_value = fake_cursor

    # Patch the django.db.connection used inside the command
    # Patch django.db module with a dummy object exposing connection
    monkeypatch.setitem(sys.modules, "django.db", MagicMock(connection=fake_conn))

    # Run command handle — should not raise
    cmd = mod.Command()
    cmd.handle()
