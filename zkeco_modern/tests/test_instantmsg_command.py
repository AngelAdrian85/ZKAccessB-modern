import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock



def test_instantmsg_calls_monitor(monkeypatch):
    repo_root = Path(__file__).resolve().parents[2]
    cmd_path = repo_root / "zkeco" / "units" / "adms" / "mysite" / "worktable" / "management" / "commands" / "instantmsg.py"
    spec = importlib.util.spec_from_file_location("worktable.instantmsg_local", str(cmd_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    # Patch the legacy monitor function if present in its module path
    fake_monitor = MagicMock()
    fake_common = MagicMock(monitor_instant_msg=fake_monitor)
    monkeypatch.setitem(sys.modules, "mysite.worktable.common_panel", fake_common)

    cmd = mod.Command()
    cmd.handle()

    assert fake_monitor.called
