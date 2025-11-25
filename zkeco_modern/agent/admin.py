from django.contrib import admin
from .models import DeviceRealtimeLog, DeviceEventLog


@admin.register(DeviceRealtimeLog)
class DeviceRealtimeLogAdmin(admin.ModelAdmin):
    list_display = ("id", "device_id", "sn", "created_at")
    list_filter = ("created_at",)
    search_fields = ("sn", "raw")
    ordering = ("-id",)


@admin.register(DeviceEventLog)
class DeviceEventLogAdmin(admin.ModelAdmin):
    list_display = ("id", "device_id", "sn", "code", "timestamp_str", "created_at")
    list_filter = ("code", "created_at")
    search_fields = ("sn", "raw_line")
    ordering = ("-id",)
