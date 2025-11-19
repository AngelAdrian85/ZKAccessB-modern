"""Compatibility package for legacy `mysite.iclock` modules.

Stubs are provided in submodules; if a real legacy `iclock` package is present
on sys.path it will be preferred automatically by normal import resolution.
"""

try:
    import importlib
    legacy = importlib.import_module('iclock')
    for _n in dir(legacy):
        if not _n.startswith('_'):
            globals()[_n] = getattr(legacy, _n)
except Exception:
    pass
