from django.db import models


class Dept(models.Model):
    code = models.CharField(max_length=32, blank=True, null=True)
    DeptName = models.CharField(max_length=128)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.DeptName


class Area(models.Model):
    areaname = models.CharField(max_length=128)

    def __str__(self):
        return self.areaname


class Employee(models.Model):
    userid = models.IntegerField(unique=True)
    badgenumber = models.CharField(max_length=32, blank=True, null=True)
    firstname = models.CharField(max_length=64, blank=True, null=True)
    lastname = models.CharField(max_length=64, blank=True, null=True)
    gender = models.CharField(max_length=16, blank=True, null=True)
    defaultdept = models.ForeignKey(Dept, on_delete=models.SET_NULL, null=True, blank=True)
    card_number = models.CharField(max_length=64, blank=True, null=True)
    site_code = models.CharField(max_length=32, blank=True, null=True)
    pager = models.CharField(max_length=32, blank=True, null=True)
    hiredday = models.DateField(null=True, blank=True)
    # Additional fields inferred from legacy exports/templates
    Password = models.CharField(max_length=128, blank=True, null=True)
    identitycard = models.CharField(max_length=64, blank=True, null=True)
    FPHONE = models.CharField(max_length=32, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    homeaddress = models.CharField(max_length=256, blank=True, null=True)
    street = models.CharField(max_length=256, blank=True, null=True)
    acc_startdate = models.DateField(null=True, blank=True)
    acc_enddate = models.DateField(null=True, blank=True)
    extend_time = models.IntegerField(null=True, blank=True)
    delayed_door_open = models.BooleanField(default=False)
    Privilege = models.CharField(max_length=64, blank=True, null=True)
    selfpassword = models.CharField(max_length=64, blank=True, null=True)
    hiretype = models.CharField(max_length=32, blank=True, null=True)
    emptype = models.CharField(max_length=32, blank=True, null=True)
    # Newly added extended fields bridging legacy UI requirements
    reservation_password = models.CharField(max_length=64, blank=True, null=True)
    role_on_device = models.CharField(max_length=64, blank=True, null=True)
    elevator_superuser = models.BooleanField(default=False)
    elevator_level = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return f"{self.userid} - {self.firstname or ''} {self.lastname or ''}".strip()


class IssueCard(models.Model):
    cardno = models.CharField(max_length=64, unique=False)
    cardstatus = models.CharField(max_length=32, blank=True, null=True)
    userid = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)
    # possible additional attributes
    card_type = models.CharField(max_length=64, blank=True, null=True)
    valid_until = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.cardno


class Device(models.Model):
    sn = models.CharField(max_length=128, blank=True, null=True)
    device_name = models.CharField(max_length=128, blank=True, null=True)
    device_type = models.IntegerField(default=0)
    comm_type = models.CharField(max_length=32, blank=True, null=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    fw_version = models.CharField(max_length=64, blank=True, null=True)
    # Additional device fields referenced in templates
    com_port = models.CharField(max_length=64, blank=True, null=True)
    com_address = models.CharField(max_length=128, blank=True, null=True)
    fp_count = models.IntegerField(null=True, blank=True)
    transaction_count = models.IntegerField(null=True, blank=True)
    acpanel_type = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return self.device_name or self.sn or str(self.pk)


class Door(models.Model):
    name = models.CharField(max_length=128)
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class AccessLog(models.Model):
    """A lightweight access/event log model for migrated access events.

    Fields are intentionally permissive (nullable) because legacy data is
    often incomplete. This model is used by the scaffolded Access Logs UI
    and by ETL imports when action/event history is imported.
    """
    timestamp = models.DateTimeField(null=True, blank=True)
    userid = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    cardno = models.CharField(max_length=64, blank=True, null=True)
    door = models.ForeignKey(Door, on_delete=models.SET_NULL, null=True, blank=True)
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=64, blank=True, null=True)
    result = models.CharField(max_length=32, blank=True, null=True)
    info = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        ts = self.timestamp.isoformat() if self.timestamp else 'n/a'
        return f"{ts} {self.userid or self.cardno or ''} {self.door or ''}".strip()
