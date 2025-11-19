"""Shim for `mysite.iclock.models.model_cmmdata` used in tests.

Provides a safe `process_writedata` callable used by some legacy commands.
Tests may monkeypatch this module, so keep the implementation minimal.
"""

def process_writedata(*args, **kwargs):
    """No-op placeholder for device write processing."""
    return None

__all__ = ['process_writedata']
