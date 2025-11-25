#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys

# Remove legacy or external project paths that can inject incompatible .pyc files
# (e.g. old vendor 'python-support' folders or Python2 site-packages). This helps
# avoid "bad magic number" errors when those folders appear earlier on sys.path.
bad_path_markers = ("ZKTeco", "python-support", "Python26")
sys.path[:] = [
    p for p in sys.path if not (p and any(marker in p for marker in bad_path_markers))
]


def main():
    """Run administrative tasks."""
    # Force override any legacy DJANGO_SETTINGS_MODULE to prevent accidental use of 'mysite.settings'
    os.environ["DJANGO_SETTINGS_MODULE"] = "zkeco_config.settings"
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
