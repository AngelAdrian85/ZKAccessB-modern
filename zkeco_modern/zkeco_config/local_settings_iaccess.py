"""Local settings for safe, local-only iaccess migrations.

This file imports the main settings and appends the legacy 'zkeco' tree
to sys.path (if present) and adds the legacy 'iaccess' app to
INSTALLED_APPS so we can run makemigrations/migrate against a local
SQLite database for iterative porting work.

Do NOT enable or commit to production; this is strictly for local dev.
"""
from __future__ import annotations
import sys
from pathlib import Path
import os

from .settings import *  # noqa: F401,F403  (import base settings)

# Ensure legacy tree is importable for makemigrations. Prefer adding the
# concrete "mysite" folder where legacy apps live so they can be imported
# as top-level packages (e.g. `import iaccess`).
legacy_root = BASE_DIR.parent / "zkeco"
legacy_mysite = legacy_root / "units" / "adms" / "mysite"
if legacy_mysite.exists():
    p = str(legacy_mysite)
    if p not in sys.path:
        sys.path.insert(0, p)
else:
    # fallback to adding the top-level legacy root (less ideal)
    if legacy_root.exists():
        p = str(legacy_root)
        if p not in sys.path:
            sys.path.insert(0, p)

# Append legacy apps we want to migrate locally
_legacy_apps = [
    "iaccess",
    # add other legacy app package names here if you want to migrate them too
]
for a in _legacy_apps:
    if a not in INSTALLED_APPS:
        INSTALLED_APPS.append(a)

# Register reconstructed legacy models app so we can create migrations locally
if "legacy_models" not in INSTALLED_APPS:
    INSTALLED_APPS.append("legacy_models")

# Include the local shim app that provides minimal views for legacy templates.
if "iaccess_port" not in INSTALLED_APPS:
    INSTALLED_APPS.append("iaccess_port")

# Keep debug on for local iterative work
DEBUG = True

# Use the existing DATABASES (default is sqlite in base settings)
# Ensure a simple secret for the local DB
SECRET_KEY = os.environ.get("LOCAL_SECRET_KEY", SECRET_KEY)

# Register legacy templatetag builtins so legacy templates can use filters/tags
try:
    builtins = TEMPLATES[0]["OPTIONS"].setdefault("builtins", [])
    for mod in (
        "legacy_models.templatetags.legacy_filters",
        "legacy_models.templatetags.legacy_defaulttags",
        "legacy_models.templatetags.legacy_shims",
    ):
        if mod not in builtins:
            builtins.append(mod)
    # also include i18n builtins so {% trans %} and related tags work
    if "django.templatetags.i18n" not in builtins:
        builtins.append("django.templatetags.i18n")
except Exception:
    pass
