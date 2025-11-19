"""Fallback `mysite.iclock.attcalc` module.

Tests expect this module to be importable and to expose `auto_calculate`.
Provide a harmless no-op implementation; tests often monkeypatch this symbol.
"""

def auto_calculate(*args, **kwargs):
    """No-op auto calculation hook for legacy compatibility."""
    return None

__all__ = ['auto_calculate']
