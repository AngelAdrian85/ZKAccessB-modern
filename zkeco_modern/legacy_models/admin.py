from django.contrib import admin
from .models import Dept, Area, Employee, IssueCard, Device, Door


@admin.register(Dept)
class DeptAdmin(admin.ModelAdmin):
    list_display = ('id', 'DeptName', 'code')


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('id', 'areaname')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('userid', 'badgenumber', 'firstname', 'lastname', 'defaultdept')
    search_fields = ('firstname', 'lastname', 'badgenumber')


@admin.register(IssueCard)
class IssueCardAdmin(admin.ModelAdmin):
    list_display = ('cardno', 'cardstatus', 'userid')


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('id', 'device_name', 'sn', 'device_type', 'area')


@admin.register(Door)
class DoorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'device')
