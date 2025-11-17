"""
URL configuration for zkeco_config project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Redirect site root to admin for convenience in development
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
]

if settings.DEBUG:
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))
