"""
Django settings for zkeco_config project.
"""

import sys
from pathlib import Path
import os

# Remove legacy or external project paths that can inject incompatible .pyc files
# (e.g. old vendor 'python-support' folders or Python2 site-packages). This helps
# avoid "bad magic number" errors when those folders appear earlier on sys.path.
bad_path_markers = (
    "ZKTeco",
    "python-support",
    "Python26",
    os.path.join("zkeco", "units"),
)
sys.path[:] = [
    p for p in sys.path if not (p and any(marker in p for marker in bad_path_markers))
]


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Optional: enable importing legacy 'zkeco' unit apps for local exploration.
# Set environment variable INCLUDE_LEGACY=1 to allow adding the legacy 'zkeco' folder
# to sys.path. This is intentionally opt-in and should NOT be enabled in production.
if os.environ.get("INCLUDE_LEGACY") == "1":
    legacy_root = BASE_DIR.parent / "zkeco"
    if legacy_root.exists():
        sys.path.insert(0, str(legacy_root))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-your-secret-key-here"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS: list[str] = []

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Legacy models shim app used for tests and legacy ETL
    "legacy_models",
    "django_extensions",
    "debug_toolbar",
]

# When opting into legacy exploration, enable the local stub app which
# renders legacy templates for demo purposes.
if os.environ.get("INCLUDE_LEGACY") == "1":
    # Only add the `legacy_stub` app to INSTALLED_APPS if `legacy_models`
    # is not already present; when `legacy_models` exists it provides
    # equivalent templatetags and models and adding the stub causes
    # duplicate template-tag registrations (templates.E003 warnings).
    try:
        import importlib.util
        if importlib.util.find_spec('legacy_models') is None:
            INSTALLED_APPS.append("legacy_stub")
    except Exception:
        # best-effort: if importlib fails, fall back to appending the stub
        INSTALLED_APPS.append("legacy_stub")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "zkeco_config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# If enabling legacy exploration, add the legacy templates folder to TEMPLATES DIRS
if os.environ.get("INCLUDE_LEGACY") == "1":
    legacy_templates = BASE_DIR.parent / 'zkeco' / 'units' / 'adms' / 'mysite' / 'templates'
    if legacy_templates.exists():
        TEMPLATES[0]["DIRS"].insert(0, str(legacy_templates))
    # register legacy templatetag builtins, but avoid duplicates when the
    # same tag module exists under `legacy_models.templatetags` (this avoids
    # templates.E003 warnings about the same tag name being provided twice).
    try:
        import importlib.util

        builtins = TEMPLATES[0]["OPTIONS"].setdefault("builtins", [])
        # candidate tag module basenames we expose from legacy_stub
        tag_names = [
            "legacy_filters",
            "dbapp_tags",
            "dbadmin_tags",
            "personnel_tags",
            "visitor_tags",
        ]
        for name in tag_names:
            legacy_models_mod = f"legacy_models.templatetags.{name}"
            legacy_stub_mod = f"legacy_stub.templatetags.{name}"
            # Prefer the templatetag modules from `legacy_models` when present.
            # If not present, fall back to the `legacy_stub` equivalents.
            try:
                if importlib.util.find_spec(legacy_models_mod) is not None:
                    if legacy_models_mod not in builtins:
                        builtins.append(legacy_models_mod)
                else:
                    if legacy_stub_mod not in builtins:
                        builtins.append(legacy_stub_mod)
            except Exception:
                # best-effort: if importlib fails, fall back to adding stub
                if legacy_stub_mod not in builtins:
                    builtins.append(legacy_stub_mod)

        # also expose a small compatibility module providing legacy block tags
        # (e.g. `ifequal`) if not available in `legacy_models`.
        try:
            compat_name = 'legacy_compat'
            legacy_models_compat = f"legacy_models.templatetags.{compat_name}"
            legacy_stub_compat = f"legacy_stub.templatetags.{compat_name}"
            if importlib.util.find_spec(legacy_models_compat) is not None:
                if legacy_models_compat not in builtins:
                    builtins.append(legacy_models_compat)
            else:
                if legacy_stub_compat not in builtins:
                    builtins.append(legacy_stub_compat)
        except Exception:
            # best-effort: fall back to adding stub compat module
            if 'legacy_stub_compat' in locals() and legacy_stub_compat not in builtins:
                builtins.append(legacy_stub_compat)
    except Exception:
        pass

    # If legacy exploration is enabled, point MEDIA settings at the legacy media
    # folder so the development server can serve old CSS/JS/images referenced
    # by the legacy templates (they use `/media/...` URLs).
    legacy_media = BASE_DIR.parent / 'zkeco' / 'units' / 'adms' / 'mysite' / 'media'
    if legacy_media.exists():
        MEDIA_URL = "/media/"
        MEDIA_ROOT = str(legacy_media)

WSGI_APPLICATION = "zkeco_config.wsgi.application"

# Database
# For development, use SQLite to avoid MySQL dependency issues

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Optional: allow overriding database with environment variables for production (Postgres)
# Set environment variables: DB_ENGINE=postgres DB_NAME=... DB_USER=... DB_PASSWORD=... DB_HOST=... DB_PORT=...
if os.environ.get("DB_ENGINE") == "postgres" or os.environ.get("USE_POSTGRES") == "1":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": os.environ.get("DB_NAME", "zkeco_db"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Debug toolbar settings
INTERNAL_IPS = [
    "127.0.0.1",
]
