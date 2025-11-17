"""Verify that core dependencies can be imported and print versions.

Run from the project root with the virtualenv activated.
"""

import importlib
import sys

# Remove legacy or external project paths that can inject incompatible .pyc files
# (same filter as in manage.py). This makes this verification script reliable
# even when older vendor folders exist on the machine's PYTHONPATH.
bad_path_markers = ("ZKTeco", "python-support", "Python26")
sys.path[:] = [
    p for p in sys.path if not (p and any(marker in p for marker in bad_path_markers))
]

packages = {
    "django": "django",
    "mysqlclient (MySQLdb)": "MySQLdb",
    "django-debug-toolbar": "debug_toolbar",
    "django-extensions": "django_extensions",
}

for pretty, modname in packages.items():
    try:
        mod = importlib.import_module(modname)
        ver = getattr(mod, "__version__", None)
        # django has get_version()
        if modname == "django":
            ver = mod.get_version()
        if ver is None:
            ver = "unknown"
        print(f"{pretty}: OK (version={ver})")
    except Exception as e:
        print(f"{pretty}: FAIL — {e}")

print("\nPython:", sys.version.replace("\n", " "))
