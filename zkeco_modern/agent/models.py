from django.db import models


class DeviceRealtimeLog(models.Model):
    device_id = models.IntegerField()
    sn = models.CharField(max_length=64, blank=True, default="")
    raw = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'agent'
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
        app_label = 'agent'
        indexes = [
            models.Index(fields=["device_id", "created_at"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):  # pragma: no cover
        return f"Evt {self.device_id} {self.code} {self.timestamp_str}"[:80]


class Device(models.Model):
    COMM_MODE_CHOICES = [
        ('tcp', 'TCP/IP'),
        ('rs485', 'RS485'),
    ]
    
    PANEL_TYPE_CHOICES = [
        ('access_panel', 'Access Control Panel'),
        ('door_controller', 'Door Controller'),
        ('biometric_reader', 'Biometric Reader'),
        ('two_door_panel', 'Two-Door Access Control Panel'),
        ('multi_door_panel', 'Multi-Door Access Control Panel'),
    ]
    
    # Basic identification
    name = models.CharField(max_length=128, help_text="Device display name (e.g., FINANCIAR, MEDICAL)")
    serial_number = models.CharField(max_length=64, blank=True, default='', unique=True, help_text="Device serial number for identification")
    device_type = models.CharField(max_length=64, choices=PANEL_TYPE_CHOICES, default='access_panel')
    
    # Communication parameters
    comm_mode = models.CharField(max_length=10, choices=COMM_MODE_CHOICES, default='tcp', help_text="TCP/IP or RS485")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address for TCP/IP devices")
    port = models.IntegerField(default=4370, help_text="Communication port (default 4370 for ZK)")
    comm_password = models.CharField(max_length=128, blank=True, default='', help_text="Device communication password")
    
    # RS485 parameters (if applicable)
    rs485_port = models.CharField(max_length=20, blank=True, default='COM1', help_text="Serial port for RS485 (e.g., COM1, /dev/ttyUSB0)")
    rs485_baudrate = models.IntegerField(default=9600, help_text="Baud rate for RS485")
    rs485_address = models.IntegerField(null=True, blank=True, help_text="Device address on RS485 bus")
    
    # Location and grouping
    area_name = models.CharField(max_length=128, blank=True, default='', help_text="Physical area/location")
    time_zone = models.CharField(max_length=50, blank=True, default='', help_text="Device time zone")
    
    # Status and configuration
    enabled = models.BooleanField(default=True, help_text="Is device enabled for polling")
    auto_sync_time = models.BooleanField(default=True, help_text="Automatically sync time to device")
    clear_on_add = models.BooleanField(default=False, help_text="Clear device data when adding to system")
    
    # Technical details
    firmware_version = models.CharField(max_length=64, blank=True, default='', help_text="Firmware version")
    hardware_version = models.CharField(max_length=64, blank=True, default='', help_text="Hardware version")
    
    # Scanner linkage (ACP/Elatec readers use these devices)
    scanner_linked = models.BooleanField(default=False, help_text="Device is used by card scanners")
    scanner_type = models.CharField(max_length=16, blank=True, default='', help_text="Scanner type: acp/elatec")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_contact = models.DateTimeField(null=True, blank=True, help_text="Last successful communication")

    class Meta:
        indexes = [
            models.Index(fields=["serial_number"]),
            models.Index(fields=["ip_address"]),
            models.Index(fields=["enabled"]),
            models.Index(fields=["scanner_linked"]),
        ]
        verbose_name = "Access Control Device"
        verbose_name_plural = "Access Control Devices"

    def __str__(self):
        return f"{self.name} (SN:{self.serial_number})"[:80]

    # Classification helpers for UI/filters
    def is_controller(self):
        return (self.device_type in ('access_panel', 'door_controller', 'two_door_panel', 'multi_door_panel')) and (not self.scanner_linked)

    def is_reader(self):
        return bool(self.scanner_linked)

    def type_badge(self):
        if self.is_reader():
            if self.scanner_type == 'acp':
                return 'Reader: ACP'
            if self.scanner_type == 'elatec':
                return 'Reader: Elatec'
            return 'Reader'
        if self.is_controller():
            return 'Centrală'
        return 'Dispozitiv'


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
    # Core identification
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    card_number = models.CharField(max_length=32, unique=True)
    access_levels = models.ManyToManyField(AccessLevel, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Legacy bridge fields
    legacy_userid = models.IntegerField(null=True, blank=True, unique=True, help_text="Identificator numeric unic din sistemul vechi")
    dept_id = models.IntegerField(null=True, blank=True, help_text="ID Departament (referință la legacy Dept)")
    
    # Personal information
    gender = models.CharField(max_length=16, blank=True, default='', help_text="Gen (M/F)")
    ssn = models.CharField(max_length=64, blank=True, default='', help_text="Social Security Number")
    birthday = models.DateField(null=True, blank=True, help_text="Data nașterii")
    city = models.CharField(max_length=128, blank=True, default='', help_text="Oraș")
    
    # Contact information
    mobile_phone = models.CharField(max_length=32, blank=True, default='', help_text="Telefon mobil")
    home_phone = models.CharField(max_length=32, blank=True, default='', help_text="Telefon acasă")
    phone = models.CharField(max_length=32, blank=True, default='', help_text="Telefon birou")
    email = models.EmailField(max_length=128, blank=True, default='', help_text="Email contact")
    
    # Address information
    homeaddress = models.CharField(max_length=256, blank=True, default='', help_text="Adresă domiciliu")
    street = models.CharField(max_length=256, blank=True, default='', help_text="Stradă / detaliu adresă")
    identitycard = models.CharField(max_length=64, blank=True, default='', help_text="Adresă de lucru")
    
    # Card and access information
    card_type = models.CharField(max_length=64, blank=True, default='', help_text="Tip card (WITH/WITHOUT Site Code)")
    site_code = models.CharField(max_length=32, blank=True, default='', help_text="Cod / prefix card (site)")
    secondary_card_number = models.CharField(max_length=32, null=True, blank=True, unique=True, help_text="Card secundar")
    password_on_record = models.CharField(max_length=32, blank=True, default='', help_text="Parolă 6 cifre")
    reservation_password = models.CharField(max_length=64, blank=True, default='123456', help_text="Parolă rezervare / acces secundar")
    selfpassword = models.CharField(max_length=64, blank=True, default='', help_text="Parolă autogestiune (opțional)")
    
    # Employment information
    hire_date = models.DateField(null=True, blank=True, help_text="Data angajării în companie")
    hiretype = models.CharField(max_length=32, blank=True, default='', help_text="Tip angajare")
    emptype = models.CharField(max_length=32, blank=True, default='', help_text="Tip personal")
    privilege = models.CharField(max_length=64, blank=True, default='', help_text="Nivel de privilegiu/rol")
    role_on_device = models.CharField(max_length=64, blank=True, default='', help_text="Rol pe dispozitiv")
    
    # Access control settings
    acc_startdate = models.DateField(null=True, blank=True, help_text="Data început valabilitate acces")
    acc_enddate = models.DateField(null=True, blank=True, help_text="Data sfârșit valabilitate acces")
    extend_time = models.IntegerField(null=True, blank=True, help_text="Extensie timp suplimentar (1-254)")
    delayed_door_open = models.BooleanField(default=False, help_text="Are întârziere la deschiderea ușii")
    access_superuser = models.BooleanField(default=False, help_text="Superuser acces")
    
    # Elevator control settings
    elevator_superuser = models.BooleanField(default=False, help_text="Acces special lift")
    elevator_level = models.CharField(max_length=64, blank=True, default='', help_text="Nivel / grup lift")
    
    # Multi-card support
    multi_card_group = models.CharField(max_length=64, blank=True, default='', help_text="Grup multi-card")
    set_validity = models.BooleanField(default=False, help_text="Setează validitate")

    class Meta:
        indexes = [
            models.Index(fields=["card_number"]),
            models.Index(fields=["legacy_userid"]),
        ]

    def __str__(self):  # pragma: no cover
        return f"Employee {self.first_name} {self.last_name}"[:80]
    
    @property
    def dept(self):
        """Get Department object from legacy_models.Dept by dept_id"""
        if not self.dept_id:
            return None
        try:
            from legacy_models.models import Dept
            return Dept.objects.get(id=self.dept_id)
        except Exception:
            return None

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


class AuditLog(models.Model):
    """Audit trail for CRUD operations on Personnel, Departments, and Cards.
    
    Stores who did what, when, on which entity, with details about changes.
    Used by Personnel module Journal feature to show modification history.
    """
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.CharField(max_length=128, blank=True, null=True)  # Username who made the change
    module = models.CharField(max_length=32, db_index=True)  # 'employee', 'department', 'issuecard'
    action = models.CharField(max_length=32)  # 'create', 'update', 'delete'
    entity_id = models.IntegerField(db_index=True)  # ID of the affected record (legacy_userid for Employee)
    entity_name = models.CharField(max_length=256, blank=True, null=True)  # Name/description for display
    details = models.TextField(blank=True, null=True)  # JSON or text with change details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        app_label = 'agent'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['module', 'entity_id', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M')} | {self.module} | {self.action} | {self.entity_name or self.entity_id}"
