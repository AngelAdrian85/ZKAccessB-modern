import os
import django
from django.test import TestCase


class LegacyModelsSmoke(TestCase):
    def test_create_basic_objects(self):
        from legacy_models.models import Dept, Area, Employee, Device, IssueCard

        d = Dept.objects.create(DeptName='Test Dept', code='T')
        a = Area.objects.create(areaname='Test Area')
        e = Employee.objects.create(userid=9999, firstname='T', lastname='User', defaultdept=d)
        dev = Device.objects.create(sn='SNX', device_name='DevX', area=a)
        ic = IssueCard.objects.create(cardno='C9999', cardstatus='1', userid=e)

        self.assertEqual(Dept.objects.count(), 1)
        self.assertEqual(Area.objects.count(), 1)
        self.assertEqual(Employee.objects.filter(userid=9999).exists(), True)
        self.assertIn('DevX', str(dev))
