"""Minimal shim for legacy `mysite.worktable.common_panel`.

Contains a no-op `monitor_instant_msg` function used by legacy management
commands. Tests commonly monkeypatch this module, so keep an intentionally
small surface area.
"""

def monitor_instant_msg(*args, **kwargs):
    """No-op monitor hook; legacy code/tests may patch this."""
    return None
