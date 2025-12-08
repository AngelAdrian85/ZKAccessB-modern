from django.contrib import admin
from .models import Area, Device, Door, Dept


@admin.register(Dept)
class DeptAdmin(admin.ModelAdmin):
    list_display = ('id', 'DeptName', 'code')


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('id', 'areaname')


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('id', 'device_name', 'sn', 'device_type', 'area')


@admin.register(Door)
class DoorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'device')
