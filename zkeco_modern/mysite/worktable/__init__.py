"""Compatibility package for legacy `mysite.worktable` modules.

This package provides lightweight fallbacks used during local migration and testing.
If the real legacy package is available on sys.path (when `INCLUDE_LEGACY=1`),
those modules will be imported instead; otherwise the no-op stubs here are used.
"""

try:
    # If a real legacy package was added to sys.path, prefer it by re-exporting
    import importlib
    legacy = importlib.import_module('worktable')
    # If successful, rebind names in this package to the legacy package attributes
    for _name in dir(legacy):
        if not _name.startswith('_'):
            globals()[_name] = getattr(legacy, _name)
except Exception:
    # no legacy package available; keep local stubs in submodules
    pass
