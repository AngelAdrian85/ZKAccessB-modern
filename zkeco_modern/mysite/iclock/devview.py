"""Compatibility shim for `mysite.iclock.devview`.

Provides a minimal `write_data` function used by some legacy management
commands. The implementation is intentionally a no-op to avoid side effects
during local testing and migration.
"""

def write_data(*args, **kwargs):
    """No-op device write helper."""
    return None

__all__ = ['write_data']
