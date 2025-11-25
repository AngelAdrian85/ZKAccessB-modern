from django.db import models


class DeviceRealtimeLog(models.Model):
    device_id = models.IntegerField()
    sn = models.CharField(max_length=64, blank=True, default="")
    raw = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["device_id", "created_at"]),
        ]

    def __str__(self):  # pragma: no cover
        return f"RTLog {self.device_id} {self.created_at}"[:80]


class DeviceEventLog(models.Model):
    device_id = models.IntegerField()
    sn = models.CharField(max_length=64, blank=True, default="")
    timestamp_str = models.CharField(max_length=32, blank=True, default="")
    code = models.CharField(max_length=32, blank=True, default="")
    raw_line = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["device_id", "created_at"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):  # pragma: no cover
        return f"Evt {self.device_id} {self.code} {self.timestamp_str}"[:80]


class Device(models.Model):
    name = models.CharField(max_length=128)
    device_type = models.CharField(max_length=64, default='Access Control Panel')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    area_name = models.CharField(max_length=64, blank=True, default='')
    enabled = models.BooleanField(default=True)
    serial_number = models.CharField(max_length=64, blank=True, default='')
    firmware_version = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["serial_number"]),
            models.Index(fields=["ip_address"]),
        ]

    def __str__(self):  # pragma: no cover
        return f"Device {self.name} ({self.serial_number})"[:80]


class DeviceStatus(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    online = models.BooleanField(default=True)
    door_state = models.CharField(max_length=32, default='CLOSED')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["device", "updated_at"]),
        ]

    def __str__(self):  # pragma: no cover
        return f"Status dev={self.device_id} online={self.online} door={self.door_state}"[:80]


# ---- New CRUD Entities ----

class Door(models.Model):
    name = models.CharField(max_length=128)
    device = models.ForeignKey(Device, null=True, blank=True, on_delete=models.SET_NULL)
    location = models.CharField(max_length=128, blank=True, default='')
    normally_open = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    is_open = models.BooleanField(default=False)  # persisted simulated state
    last_state_change = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["name"])]

    def __str__(self):  # pragma: no cover
        return f"Door {self.name}"[:80]


class TimeSegment(models.Model):
    name = models.CharField(max_length=64)
    start_time = models.TimeField()
    end_time = models.TimeField()
    # Bitmask for days of week (0=Mon .. 6=Sun). Default: all days (0b1111111 = 127)
    days_mask = models.PositiveSmallIntegerField(default=127)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["name"])]

    def clean(self):
        if self.start_time >= self.end_time:
            from django.core.exceptions import ValidationError
            raise ValidationError("Start time must be before end time")
        # Basic overlap validation: any other segment whose range intersects ours
        # (Global scope; could be scoped per door/access level later.)
        if self.pk is None:
            existing = TimeSegment.objects.all()
        else:
            existing = TimeSegment.objects.exclude(pk=self.pk)
        for other in existing:
            if other.start_time < self.end_time and other.end_time > self.start_time:
                # Only consider overlap if days intersect
                if other.days_mask & self.days_mask:
                    from django.core.exceptions import ValidationError
                    raise ValidationError(f"Time segment '{other.name}' overlaps with this range on shared days")

    def __str__(self):  # pragma: no cover
        return f"Segment {self.name} {self.start_time}-{self.end_time}"[:80]

    def days_display(self):  # pragma: no cover
        names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        active = []
        for i, n in enumerate(names):
            if self.days_mask & (1 << i):
                active.append(n)
        return ",".join(active)


class Holiday(models.Model):
    name = models.CharField(max_length=64)
    date = models.DateField(unique=True)
    description = models.CharField(max_length=256, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date"]
        indexes = [models.Index(fields=["date"])]

    def __str__(self):  # pragma: no cover
        return f"Holiday {self.name} {self.date}"[:80]


class AccessLevel(models.Model):
    name = models.CharField(max_length=64, unique=True)
    doors = models.ManyToManyField(Door, blank=True)
    time_segments = models.ManyToManyField(TimeSegment, blank=True)
    description = models.CharField(max_length=256, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["name"])]

    def __str__(self):  # pragma: no cover
        return f"AccessLevel {self.name}"[:80]


class Employee(models.Model):
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    card_number = models.CharField(max_length=32, unique=True)
    access_levels = models.ManyToManyField(AccessLevel, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["card_number"])]

    def __str__(self):  # pragma: no cover
        return f"Employee {self.first_name} {self.last_name}"[:80]


class EmployeeCard(models.Model):
    employee = models.ForeignKey(
        Employee, related_name="cards", on_delete=models.CASCADE
    )
    card_number = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["card_number"]),
            models.Index(fields=["employee"]),
        ]

    def __str__(self):  # pragma: no cover
        return f"Card {self.card_number} for {self.employee}"[:80]


class CommandLog(models.Model):
    device = models.ForeignKey(Device, null=True, blank=True, on_delete=models.SET_NULL)
    door = models.ForeignKey(Door, null=True, blank=True, on_delete=models.SET_NULL)
    command = models.CharField(max_length=64)
    status = models.CharField(max_length=16, default='PENDING')  # PENDING/OK/ERR
    result = models.CharField(max_length=128, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["created_at"]), models.Index(fields=["status"])]

    def __str__(self):  # pragma: no cover
        return f"Cmd {self.command} {self.status}"[:80]


class EmployeeAccessCache(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    door = models.ForeignKey(Door, on_delete=models.CASCADE)
    allowed = models.BooleanField(default=False)
    reason = models.CharField(max_length=64)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("employee", "door")
        indexes = [models.Index(fields=["employee","door"]), models.Index(fields=["updated_at"])]

    def __str__(self):  # pragma: no cover
        return f"Cache emp={self.employee_id} door={self.door_id} {self.allowed}"[:80]
