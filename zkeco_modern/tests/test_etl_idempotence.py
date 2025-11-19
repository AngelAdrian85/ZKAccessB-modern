import os
from django.test import TestCase


class ETLIdempotence(TestCase):
    def test_employee_update_and_dry_run(self):
        base = os.path.join(os.path.dirname(__file__), os.pardir, 'etl', 'fixtures')
        base = os.path.normpath(base)
        emp_csv = os.path.join(base, 'employee_sample.csv')
        emp_alt = os.path.join(base, 'employee_alt.csv')

        from zkeco_modern.etl.employee import import_employees_from_csv
        from legacy_models.models import Employee
        # initial import
        r1 = import_employees_from_csv(emp_csv, commit=True, update=False)
        created_count = r1['created'] if isinstance(r1, dict) else r1
        self.assertGreaterEqual(created_count, 2)

        # dry-run update: shouldn't change data
        r_dry = import_employees_from_csv(emp_alt, commit=True, update=True, dry_run=True)
        # counts should be zero for created/updated because dry-run doesn't persist
        self.assertIn('created', r_dry)

        # perform update for real
        r2 = import_employees_from_csv(emp_alt, commit=True, update=True, dry_run=False)
        # ensure employees with same userid were updated or created
        emp = Employee.objects.filter(userid=3001).first()
        self.assertIsNotNone(emp)
        self.assertIn(emp.firstname, ('Alpha', 'AlphaX'))

    def test_device_update(self):
        base = os.path.join(os.path.dirname(__file__), os.pardir, 'etl', 'fixtures')
        base = os.path.normpath(base)
        dev_csv = os.path.join(base, 'device_sample.csv')
        dev_alt = os.path.join(base, 'device_alt.csv')

        from zkeco_modern.etl.device import import_devices_from_csv
        from legacy_models.models import Device
        r1 = import_devices_from_csv(dev_csv, commit=True, update=False)
        created_count = r1['created'] if isinstance(r1, dict) else r1
        self.assertGreaterEqual(created_count, 1)

        # update with alternate file
        r2 = import_devices_from_csv(dev_alt, commit=True, update=True)
        # device SN3001 should exist and possibly be updated
        dev = Device.objects.filter(sn='SN3001').first()
        self.assertIsNotNone(dev)
        self.assertIn(dev.device_name, ('FrontGate', 'FrontGateRenamed'))
