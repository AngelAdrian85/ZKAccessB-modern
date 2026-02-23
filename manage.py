#!/usr/bin/env python
"""Root-level manage.py shim for pytest-django project discovery.

Important: legacy vendor paths can inject incompatible Python2 .pyc files.
Keep sys.path filtering consistent with zkeco_modern/manage.py.
"""

import os
import sys

# Remove legacy or external project paths that can inject incompatible .pyc files
bad_path_markers = ("ZKTeco", "python-support", "Python26")
sys.path[:] = [
    p for p in sys.path if not (p and any(marker in p for marker in bad_path_markers))
]

BASE = os.path.dirname(__file__)

# Ensure modern project directory is on path
modern_dir = os.path.join(BASE, "zkeco_modern")
if modern_dir not in sys.path:
    sys.path.insert(0, modern_dir)

# Force correct settings module (override any system env)
os.environ["DJANGO_SETTINGS_MODULE"] = "zkeco_config.settings"

from django.core.management import execute_from_command_line  # type: ignore

execute_from_command_line(sys.argv)
