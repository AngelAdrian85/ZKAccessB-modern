from django.db import models


class Dept(models.Model):
    DeptName = models.CharField(max_length=200, null=True, blank=True)
    code = models.CharField(max_length=50, null=True, blank=True)
    
    def __str__(self):
        return self.DeptName or self.code or f"Dept {self.pk}"


class Area(models.Model):
    areaname = models.CharField(max_length=200, null=True, blank=True)
    
    def __str__(self):
        return self.areaname or f"Area {self.pk}"


class Employee(models.Model):
    userid = models.IntegerField(unique=True)
    firstname = models.CharField(max_length=200, null=True, blank=True)
    lastname = models.CharField(max_length=200, null=True, blank=True)
    email = models.CharField(max_length=254, null=True, blank=True)
    identitycard = models.CharField(max_length=128, null=True, blank=True)
    Password = models.CharField(max_length=128, null=True, blank=True)
    FPHONE = models.CharField(max_length=64, null=True, blank=True)
    defaultdept = models.ForeignKey(Dept, on_delete=models.SET_NULL, null=True, related_name='employees')
    
    # Legacy ETL and tests expect these fields
    badgenumber = models.CharField(max_length=64, null=True, blank=True)
    acc_startdate = models.DateField(null=True, blank=True)
    acc_enddate = models.DateField(null=True, blank=True)
    
    def __str__(self):
        name = f"{self.firstname or ''} {self.lastname or ''}".strip()
        return name or str(self.userid)


class Device(models.Model):
    sn = models.CharField(max_length=128, null=True, blank=True)
    device_name = models.CharField(max_length=200, null=True, blank=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, related_name='devices')
    
    # Additional legacy fields used by ETL/tests
    device_type = models.CharField(max_length=100, null=True, blank=True)
    fw_version = models.CharField(max_length=100, null=True, blank=True)
    com_port = models.CharField(max_length=50, null=True, blank=True)
    com_address = models.CharField(max_length=50, null=True, blank=True)
    fp_count = models.IntegerField(null=True, blank=True, default=0)
    transaction_count = models.IntegerField(null=True, blank=True, default=0)
    acpanel_type = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return self.device_name or self.sn or f"Device {self.pk}"


class IssueCard(models.Model):
    cardno = models.CharField(max_length=64, null=True, blank=True)
    cardstatus = models.CharField(max_length=20, null=True, blank=True)
    userid = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True)
    
    def __str__(self):
        return self.cardno or f"IssueCard {self.pk}"


class AccessLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    door = models.ForeignKey('Door', on_delete=models.SET_NULL, null=True)
    SN = models.CharField(max_length=128, null=True, blank=True)
    device_name = models.CharField(max_length=200, null=True, blank=True)
    
    # Legacy-style fields expected by ETL/tests
    userid = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True)
    cardno = models.CharField(max_length=64, null=True, blank=True)
    device = models.ForeignKey('Device', on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=64, null=True, blank=True)
    result = models.CharField(max_length=64, null=True, blank=True)
    info = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"AccessLog {self.pk} - {self.timestamp.isoformat()}"


class Door(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    areaname = models.CharField(max_length=200, null=True, blank=True)
    
    def __str__(self):
        return self.name or f"Door {self.pk}"


__all__ = [
    "Dept",
    "Area",
    "Employee",
    "Device",
    "IssueCard",
    "AccessLog",
    "Door",
]
