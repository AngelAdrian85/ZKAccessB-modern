"""
Django settings for zkeco_config project.
"""

import sys
from pathlib import Path
import os
import socket

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

def _compute_allowed_hosts() -> list[str]:
    hosts = {"127.0.0.1", "localhost", "testserver"}

    extra_hosts = str(os.environ.get("ZKACCESS_ALLOWED_HOSTS") or "").strip()
    if extra_hosts:
        for part in extra_hosts.split(","):
            item = part.strip()
            if item:
                hosts.add(item)

    # In local Windows deployments the controller often reaches Django by the
    # workstation's LAN IP, not by localhost. Accept the machine name/IPs so
    # /iclock/cdata is not rejected with DisallowedHost.
    try:
        hosts.add(socket.gethostname())
    except Exception:
        pass
    try:
        hosts.add(socket.getfqdn())
    except Exception:
        pass
    try:
        for name in {socket.gethostname(), socket.getfqdn()}:
            if not name:
                continue
            for family, _socktype, _proto, _canonname, sockaddr in socket.getaddrinfo(name, None):
                if family == socket.AF_INET and sockaddr and sockaddr[0]:
                    hosts.add(sockaddr[0])
    except Exception:
        pass

    return sorted(item for item in hosts if item)


ALLOWED_HOSTS: list[str] = _compute_allowed_hosts()

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "legacy_models.apps.LegacyModelsConfig",  # legacy reconstructed models
    "django_extensions",
    "agent.apps.AgentConfig",
    "iaccess_port.apps.IAccessPortConfig",
    "channels",
]

# If legacy_models cannot be imported (missing legacy 'mysite' path), drop it gracefully
try:
    import legacy_models  # type: ignore
except Exception:
    INSTALLED_APPS = [a for a in INSTALLED_APPS if a != "legacy_models.apps.LegacyModelsConfig"]

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
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "agent.middleware.SystemTimeZoneMiddleware",  # System Options time zone
    "agent.middleware.AuditMiddleware",  # Track user for audit logging
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
ASGI_APPLICATION = "zkeco_config.asgi.application"

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
TIME_ZONE = "Europe/Bucharest"  # Romania EET/EEST (UTC+2 / UTC+3)
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# Use leading slash so {% static %} resolves correctly (e.g. /static/agent/dashboard.css)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static-root"
WHITENOISE_USE_FINDERS = True

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Channels / WebSocket layer configuration with Redis fallback to in-memory.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer" if os.environ.get("REDIS_URL") else "channels.layers.InMemoryChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")]
        } if os.environ.get("REDIS_URL") else {},
    }
}

# Debug toolbar settings
INTERNAL_IPS = ["127.0.0.1"]

# Auth redirects
LOGIN_REDIRECT_URL = "/agent/dashboard/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# When DEBUG is enabled and DEBUG_TOOLBAR=1 env var is set, load debug toolbar apps/middleware dynamically.
if DEBUG and os.environ.get("DEBUG_TOOLBAR") == "1":
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

# ZKTeco controller communication password (plcommpro "passwd=")
#
# Many controllers use a numeric communication key (often "0"), but some deployments
# use a non-empty password. We keep this configurable and use it as a fallback only
# when the operator/device does not provide a password.
ZKACCESS_DEFAULT_COMM_PASSWORD = (os.environ.get("ZKACCESS_DEFAULT_COMM_PASSWORD") or "").strip()


def _env_int(name: str, default: int) -> int:
    try:
        parsed = int(str(os.environ.get(name, default)).strip())
    except Exception:
        return int(default)
    return parsed


def _env_bool(name: str, default: bool = False) -> bool:
    raw = str(os.environ.get(name, "") or "").strip().lower()
    if not raw:
        return bool(default)
    return raw in {"1", "true", "yes", "on"}


ZKACCESS_PUSH_PROTOCOL_VERSION = (os.environ.get("ZKACCESS_PUSH_PROTOCOL_VERSION") or "2.0").strip() or "2.0"
ZKACCESS_PUSH_TIMEOUT_SEC = _env_int("ZKACCESS_PUSH_TIMEOUT_SEC", 300)
ZKACCESS_PUSH_SERVER_NAME = (os.environ.get("ZKACCESS_PUSH_SERVER_NAME") or "ZKAccessB Modern").strip() or "ZKAccessB Modern"
ZKACCESS_PUSH_SERVER_VERSION = (os.environ.get("ZKACCESS_PUSH_SERVER_VERSION") or "2026.04").strip() or "2026.04"
ZKACCESS_PUSH_ENCRYPT = (os.environ.get("ZKACCESS_PUSH_ENCRYPT") or "0").strip() or "0"
ZKACCESS_PUSH_TRANS_TABLES = (os.environ.get("ZKACCESS_PUSH_TRANS_TABLES") or "transaction,ATTLOG").strip()
ZKACCESS_PUSH_TRANS_TIMES = (os.environ.get("ZKACCESS_PUSH_TRANS_TIMES") or "00:00;24:00").strip() or "00:00;24:00"
ZKACCESS_PUSH_REQUEST_DELAY = _env_int("ZKACCESS_PUSH_REQUEST_DELAY", 3)
ZKACCESS_PUSH_ERROR_DELAY = _env_int("ZKACCESS_PUSH_ERROR_DELAY", 15)
ZKACCESS_PUSH_DELAY = _env_int("ZKACCESS_PUSH_DELAY", 30)
ZKACCESS_PUSH_TRANS_INTERVAL = _env_int("ZKACCESS_PUSH_TRANS_INTERVAL", 1)
ZKACCESS_PUSH_TRANS_FLAG = _env_int("ZKACCESS_PUSH_TRANS_FLAG", 1)
ZKACCESS_PUSH_OPTION_TRANS_FLAG = (
    os.environ.get("ZKACCESS_PUSH_OPTION_TRANS_FLAG")
    or "AttLog    OpLog   AttPhoto    EnrollUser  ChgUser EnrollFP    ChgFP   Userpic"
).strip() or "AttLog    OpLog   AttPhoto    EnrollUser  ChgUser EnrollFP    ChgFP   Userpic"
ZKACCESS_PUSH_REALTIME = _env_int("ZKACCESS_PUSH_REALTIME", 1)
ZKACCESS_PUSH_RTLOG = _env_int("ZKACCESS_PUSH_RTLOG", 1)
ZKACCESS_PUSH_TIMEZONE = _env_int("ZKACCESS_PUSH_TIMEZONE", 2)
ZKACCESS_PUSH_OPTIONS_FLAG = _env_int("ZKACCESS_PUSH_OPTIONS_FLAG", 1)
ZKACCESS_PUSH_OPTIONS = (
    os.environ.get("ZKACCESS_PUSH_OPTIONS")
    or "UserCount,TransactionCount,FingerFunOn,FPVersion,FPCount,FaceFunOn,FaceVersion,FaceCount,FvFunOn,FvVersion,FvCount,PvFunOn,PvVersion,PvCount,BioPhotoFun,BioDataFun,PhotoFunOn,~LockFunOn,CardProtFormat,~Platform,MultiBioPhotoSupport,MultiBioDataSupport,MultiBioVersion,MaskDetectionFunOn"
).strip()
ZKACCESS_PUSH_ATTLOG_STAMP = _env_int("ZKACCESS_PUSH_ATTLOG_STAMP", 0)
ZKACCESS_PUSH_OPERLOG_STAMP = _env_int("ZKACCESS_PUSH_OPERLOG_STAMP", 0)
ZKACCESS_PUSH_ATTPHOTO_STAMP = _env_int("ZKACCESS_PUSH_ATTPHOTO_STAMP", 0)
ZKACCESS_PUSH_ERRORLOG_STAMP = _env_int("ZKACCESS_PUSH_ERRORLOG_STAMP", 0)
ZKACCESS_PUSH_PUBLIC_SCHEME = (os.environ.get("ZKACCESS_PUSH_PUBLIC_SCHEME") or "http").strip().lower() or "http"
ZKACCESS_PUSH_PUBLIC_HOST = (os.environ.get("ZKACCESS_PUSH_PUBLIC_HOST") or "").strip()
ZKACCESS_PUSH_PUBLIC_PORT = _env_int("ZKACCESS_PUSH_PUBLIC_PORT", 0)
ZKACCESS_PUSH_REBOOT_AFTER_CONFIG = _env_bool("ZKACCESS_PUSH_REBOOT_AFTER_CONFIG", False)
ZKACCESS_PUSH_HTTPS_ENABLED = _env_bool("ZKACCESS_PUSH_HTTPS_ENABLED", False)
ZKACCESS_TRUST_PROXY_SSL = _env_bool("ZKACCESS_TRUST_PROXY_SSL", True)

USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
if ZKACCESS_TRUST_PROXY_SSL:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
