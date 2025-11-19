"""
URL configuration for zkeco_config project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import RedirectView
import os
import sys
from pathlib import Path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Redirect site root to admin for convenience in development
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
]

# As a local-first fallback, ensure `/iaccess/` resolves by mapping directly
# to the minimal shim index view when the app is available. This helps tests
# that hit `/iaccess/` without relying on legacy include heuristics.
try:
    from iaccess_port import views as _iaccess_views
    urlpatterns.insert(0, path('iaccess/', _iaccess_views.index, name='iaccess_index_direct'))
except Exception:
    # best-effort only for local dev/tests
    pass

if settings.DEBUG:
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))

# Optionally include legacy 'zkeco' unit URLConfs when enabled for local exploration.
# Set environment variable INCLUDE_LEGACY=1 to attempt to import legacy URLs from
# the repo's top-level `zkeco/units/adms/mysite` folder. This is local-only.
if os.environ.get("INCLUDE_LEGACY") == "1":
    try:
        # Add legacy 'mysite' folder to sys.path so inner packages (like iaccess) import
        legacy_mysite = Path(__file__).resolve().parent.parent.parent / 'zkeco' / 'units' / 'adms' / 'mysite'
        if legacy_mysite.exists():
            sys.path.insert(0, str(legacy_mysite))
        # Import known legacy app url modules and include them under root
        try:
            import importlib
            # prefer to include our local stub app when available
            legacy_stub = importlib.import_module('legacy_stub.urls')
            urlpatterns.append(path('', include(legacy_stub)))
        except Exception:
            try:
                legacy_iaccess = importlib.import_module('iaccess.urls')
                urlpatterns.append(path('', include(legacy_iaccess)))
            except Exception as _e:
                # best-effort: if neither stub nor original iaccess is importable, ignore
                print('Could not include legacy iaccess URLs:', _e)
    except Exception as e:
        print('Error while attempting to include legacy URLs:', e)

# Always include our local shim `iaccess_port` URLs when the app is installed
try:
    from django.conf import settings as _s
    if 'iaccess_port' in getattr(_s, 'INSTALLED_APPS', []):
        # prefer an explicit mount at /iaccess/ so legacy routes are available
        urlpatterns.append(path('iaccess/', include('iaccess_port.urls')))
        # also include at root so patterns defined with their own 'iaccess/'
        # prefix (as the shim does) are available when included directly.
        urlpatterns.append(path('', include('iaccess_port.urls')))
except Exception:
    # best-effort: if import fails, do not break URLConf
    pass
