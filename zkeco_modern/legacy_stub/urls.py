from django.urls import path
from . import views

urlpatterns = [
    path('iaccess/', views.legacy_render, name='legacy_iaccess_root'),
    path('iaccess/<path:subpath>/', views.legacy_render, name='legacy_iaccess_sub'),
]
