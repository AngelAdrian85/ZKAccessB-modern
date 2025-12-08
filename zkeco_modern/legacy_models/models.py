from django.db import models


class Dept(models.Model):
    """Department model - temporarily kept in legacy_models until full migration to agent.Dept"""
    code = models.CharField(max_length=32, blank=True, null=True)
    DeptName = models.CharField(max_length=128)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.DeptName


class Area(models.Model):
    areaname = models.CharField(max_length=128)

    def __str__(self):
        return self.areaname


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
    userid = models.IntegerField(null=True, blank=True)  # Changed from FK to integer to avoid legacy.Employee reference
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
