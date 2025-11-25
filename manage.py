#!/usr/bin/env python
"""Root-level manage.py shim for pytest-django project discovery."""
import os, sys
BASE = os.path.dirname(__file__)
# Ensure modern project directory is on path
modern_dir = os.path.join(BASE, 'zkeco_modern')
if modern_dir not in sys.path:
    sys.path.insert(0, modern_dir)
# Force correct settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
from django.core.management import execute_from_command_line  # type: ignore
execute_from_command_line(sys.argv)
