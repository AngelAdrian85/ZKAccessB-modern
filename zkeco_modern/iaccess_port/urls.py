from django.urls import path
from . import views

urlpatterns = [
    # ORM-backed example page: employee list
    path('iaccess/employees/', views.employee_list, name='iaccess_employee_list'),
    # ORM-backed example page: device list
    path('iaccess/devices/', views.device_list, name='iaccess_device_list'),
    # ORM-backed example page: door list
    path('iaccess/doors/', views.door_list, name='iaccess_door_list'),
        path('iaccess/logs/', views.access_log, name='iaccess_access_log'),
        path('iaccess/logs/export-status/<str:job_id>/', views.export_status, name='iaccess_export_status'),
    path("iaccess/", views.index, name="iaccess_index"),
    path("iaccess/<path:subpath>/", views.render_page, name="iaccess_page"),
]
