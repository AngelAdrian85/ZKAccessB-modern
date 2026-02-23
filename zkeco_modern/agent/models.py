from django.db import models
from django.db.models import Q


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

    # Network settings (legacy parity)
    subnet_mask = models.CharField(max_length=32, blank=True, default='', help_text="Subnet mask (e.g., 255.255.255.0)")
    gateway = models.GenericIPAddressField(null=True, blank=True, help_text="Gateway address")
    
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

    def is_physical_controller(self) -> bool:
        """Best-effort: True only for real (non-test) controllers.

        Kept migration-free; used only for UI/UX gating.
        """
        try:
            if not self.is_controller():
                return False
            if not (self.ip_address or ''):
                return False
            ip = str(self.ip_address).strip()
            if not ip or ip in ('0.0.0.0',) or ip.startswith('127.'):
                return False
            name_u = (self.name or '').upper()
            sn_u = (self.serial_number or '').upper()
            if 'TEST' in name_u or 'TEST' in sn_u:
                return False
            return True
        except Exception:
            return False


class DSTime(models.Model):
    """Daylight Saving Time rules migrated from legacy DSTime model."""

    WEEK_CHOICES = [
        ('first', 'First'),
        ('second', 'Second'),
        ('third', 'Third'),
        ('fourth', 'Fourth'),
        ('last', 'Last'),
    ]

    name = models.CharField(max_length=64, unique=True)
    start_month = models.PositiveSmallIntegerField()  # 1-12
    start_week = models.CharField(max_length=8, choices=WEEK_CHOICES, default='last')
    start_weekday = models.PositiveSmallIntegerField(default=0)  # 0=Monday
    start_hour = models.PositiveSmallIntegerField(default=3)
    start_minute = models.PositiveSmallIntegerField(default=0)

    end_month = models.PositiveSmallIntegerField()
    end_week = models.CharField(max_length=8, choices=WEEK_CHOICES, default='last')
    end_weekday = models.PositiveSmallIntegerField(default=0)
    end_hour = models.PositiveSmallIntegerField(default=3)
    end_minute = models.PositiveSmallIntegerField(default=0)

    offset_minutes = models.IntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["start_month", "end_month"]),
        ]

    def __str__(self):  # pragma: no cover
        return f"DST {self.name}"[:80]


class LegacyAreaMeta(models.Model):
    """Extra metadata for legacy `legacy_models.Area` rows.

    We keep this in `agent` so we can extend area data (code/parent/remarks)
    without modifying the legacy shim schema.
    """

    legacy_area_id = models.IntegerField(unique=True, db_index=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    parent_legacy_area_id = models.IntegerField(blank=True, null=True)
    remarks = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["legacy_area_id"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):  # pragma: no cover
        return f"LegacyAreaMeta area_id={self.legacy_area_id} code={self.code or ''}"[:80]


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
    door_number = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=[(i, str(i)) for i in range(1, 33)],
        help_text="Door index on controller (1-32)",
    )
    location = models.CharField(max_length=128, blank=True, default='')
    normally_open = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    SENSOR_TYPE_CHOICES = [
        ('none', 'Niciunul'),
        ('normal_close', 'Normal închis'),
        ('normal_open', 'Normal deschis'),
    ]
    VERIFY_MODE_CHOICES = [
        ('only_card', 'Doar card'),
        ('card_pin', 'Card + PIN'),
        ('card_fingerprint', 'Card + Amprentă'),
        ('fingerprint', 'Amprentă'),
        ('face', 'Față'),
        ('multi', 'Multi-verificare'),
    ]

    # ---- Legacy-like Door Configuration fields (Door Details page)
    door_active_time_zone = models.ForeignKey(
        'TimeSegment',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='doors_active_tz',
        help_text='Door Active Time Zone (legacy Door Details)'
    )
    door_passage_mode_time_zone = models.ForeignKey(
        'TimeSegment',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='doors_passage_tz',
        help_text='Door Passage Mode Time Zone (legacy Door Details)'
    )
    lock_open_duration = models.PositiveSmallIntegerField(default=5, help_text='Lock Open Duration (0-254 seconds)')
    punch_interval = models.PositiveSmallIntegerField(default=2, help_text='Punch Interval (0-254 seconds)')
    door_sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPE_CHOICES, default='normal_close')
    door_status_delay = models.PositiveSmallIntegerField(default=15, help_text='Door Status Delay (1-254 seconds)')
    close_and_reverse_state = models.BooleanField(default=False)
    verify_mode = models.CharField(max_length=32, choices=VERIFY_MODE_CHOICES, default='only_card')
    duress_password = models.CharField(max_length=16, blank=True, default='')
    emergency_password = models.CharField(max_length=16, blank=True, default='')

    # User-defined reader names (legacy Door Details: Reader In/Out).
    # If empty, UI derives defaults from controller IP + door number.
    reader_in_custom_name = models.CharField(max_length=128, blank=True, default='')
    reader_out_custom_name = models.CharField(max_length=128, blank=True, default='')
    is_open = models.BooleanField(default=False)  # persisted simulated state
    last_state_change = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["device", "door_number"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["device", "door_number"],
                condition=Q(door_number__isnull=False),
                name="uniq_door_per_device_number",
            )
        ]

    @property
    def reader_in_name(self) -> str:
        if self.reader_in_custom_name:
            return self.reader_in_custom_name
        ip = getattr(getattr(self, 'device', None), 'ip_address', None)
        if ip and self.door_number:
            return f"{ip}-{self.door_number} In"
        return ""

    @property
    def reader_out_name(self) -> str:
        if self.reader_out_custom_name:
            return self.reader_out_custom_name
        ip = getattr(getattr(self, 'device', None), 'ip_address', None)
        if ip and self.door_number:
            return f"{ip}-{self.door_number} Out"
        return ""

    def __str__(self):  # pragma: no cover
        dn = f" #{self.door_number}" if self.door_number else ""
        return f"Door{dn} {self.name}"[:80]


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
        # NOTE: Overlap validation intentionally disabled.
        # Real deployments frequently need overlapping intervals (e.g. an 'ALWAYS' segment
        # plus narrower segments). Enforcement is done at door/access-level selection time.

    def __str__(self):  # pragma: no cover
        return f"Segment {self.name} {self.start_time}-{self.end_time}"[:80]

    def days_display(self):  # pragma: no cover
        names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        active = []
        for i, n in enumerate(names):
            if self.days_mask & (1 << i):
                active.append(n)
        return ",".join(active)


class DoorFirstCardRule(models.Model):
    """Legacy-like First-Card Normal Open rules per door.

    In old ZKAccess UI this is configured under Door Configuration -> First-Card Normal Open Setting.
    """

    door = models.ForeignKey(Door, on_delete=models.CASCADE, related_name='first_card_rules')
    time_segment = models.ForeignKey(TimeSegment, null=True, blank=True, on_delete=models.SET_NULL, related_name='first_card_rules')
    employees = models.ManyToManyField('Employee', blank=True, related_name='first_card_rules')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['door', 'created_at']),
        ]

    def __str__(self):  # pragma: no cover
        return f"FirstCard door={self.door_id} tz={getattr(self.time_segment, 'name', '')}"[:80]


class DoorMultiCardRule(models.Model):
    """Legacy-like Multi-Card Open combinations per door."""

    door = models.ForeignKey(Door, on_delete=models.CASCADE, related_name='multi_card_rules')
    name = models.CharField(max_length=128, default='', blank=True)
    required_count = models.PositiveSmallIntegerField(default=2)
    employees = models.ManyToManyField('Employee', blank=True, related_name='multi_card_rules')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['door', 'created_at']),
        ]

    def __str__(self):  # pragma: no cover
        return f"MultiCard door={self.door_id} name={self.name}"[:80]


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
    is_visitor = models.BooleanField(default=False, help_text="Nivel vizitatori (Da/Nu)")
    # Stable fingerprint for business rule: unique by (time segment + door combination).
    # Nullable to allow safe backfill during migrations; enforced in forms and DB when present.
    signature = models.CharField(max_length=64, unique=True, null=True, blank=True)
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
    slot = models.CharField(
        max_length=16,
        default='additional',
        db_index=True,
        help_text="Slot card: primary/secondary/additional",
    )
    status = models.CharField(
        max_length=20,
        default='Active',
        db_index=True,
        help_text="Stare card: Active/Inactive/Suspended",
    )
    site_code = models.CharField(max_length=32, blank=True, default='', help_text="Site code / prefix")
    valid_until = models.DateField(null=True, blank=True, help_text="Data expirare")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["card_number"]),
            models.Index(fields=["employee"]),
            models.Index(fields=["slot"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):  # pragma: no cover
        return f"Card {self.card_number} for {self.employee}"[:80]


class CommandLog(models.Model):
    device = models.ForeignKey(Device, null=True, blank=True, on_delete=models.SET_NULL)
    door = models.ForeignKey(Door, null=True, blank=True, on_delete=models.SET_NULL)
    command = models.CharField(max_length=240)
    status = models.CharField(max_length=16, default='PENDING')  # PENDING/OK/ERR
    result = models.CharField(max_length=128, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["created_at"]), models.Index(fields=["status"])]

    def __str__(self):  # pragma: no cover
        return f"Cmd {self.command} {self.status}"[:80]


class SystemSettings(models.Model):
    """Singleton-like system configuration (legacy 'System Options')."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    time_zone = models.CharField(max_length=64, blank=True, default='Etc/GMT+2')
    # UI preferences
    date_format = models.CharField(max_length=16, blank=True, default='ro_short')
    week_start = models.CharField(max_length=8, blank=True, default='monday')

    # Default device communication password (used as fallback for probes/wizard)
    default_comm_password = models.CharField(max_length=64, blank=True, default='')

    # SYNC_PERSONNEL controls (anti-DoS / performance)
    sync_personnel_enabled = models.BooleanField(default=True)
    sync_personnel_dedupe_seconds = models.PositiveSmallIntegerField(default=60)
    sync_personnel_reassert_seconds = models.PositiveIntegerField(default=21600)  # 6h
    sync_personnel_batch_size = models.PositiveIntegerField(default=200)
    sync_personnel_inter_batch_sleep = models.FloatField(default=0.02)
    sync_personnel_max_per_minute = models.PositiveSmallIntegerField(default=0)  # 0 = disabled
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_solo(cls) -> "SystemSettings":
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):  # pragma: no cover
        return f"SystemSettings tz={self.time_zone or ''}"[:80]


class TimeZoneSetting(models.Model):
    """Named time zone presets managed from System module.

    Exactly one row should be active at a time. The active row is mirrored into
    SystemSettings.time_zone.
    """

    name = models.CharField(max_length=64, unique=True)
    region = models.CharField(max_length=64, blank=True, default='')
    time_zone = models.CharField(max_length=64)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active"], name='tzs_active_idx'),
            models.Index(fields=["time_zone"], name='tzs_tz_idx'),
        ]

    def __str__(self):  # pragma: no cover
        flag = '*' if self.is_active else ''
        return f"TZSetting{flag} {self.name} {self.time_zone}"[:80]


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
