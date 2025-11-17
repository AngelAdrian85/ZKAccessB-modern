import importlib
from unittest.mock import MagicMock

import pytest


def test_autocalculate_once(monkeypatch):
    # Skip test if legacy attcalc module is not importable in this environment
    pytest.importorskip("mysite.iclock.attcalc")

    # Import the management command module
    mod = importlib.import_module(
        "zkeco.units.adms.mysite.att.management.commands.autocalculate"
    )

    # Patch the legacy auto_calculate function so we don't execute real logic
    attcalc_mod = importlib.import_module("mysite.iclock.attcalc")
    mock_auto = MagicMock()
    setattr(attcalc_mod, "auto_calculate", mock_auto)

    # Patch time.sleep to avoid delays
    monkeypatch.setattr("time.sleep", lambda s: None)

    # Run the Command.handle with once flag set via options dict
    cmd = mod.Command()
    # call handle with options containing once=True
    cmd.handle(once=True)

    # Verify auto_calculate was called at least once
    assert mock_auto.called
