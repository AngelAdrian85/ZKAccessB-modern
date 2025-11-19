import os
from django.test import TestCase


class ETLSmoke(TestCase):
    def test_etl_employee_issuecard_device(self):
        base = os.path.join(os.path.dirname(__file__), os.pardir, 'etl', 'fixtures')
        base = os.path.normpath(base)
        emp_csv = os.path.join(base, 'employee_sample.csv')
        ic_csv = os.path.join(base, 'issuecard_sample.csv')
        dev_csv = os.path.join(base, 'device_sample.csv')

        from zkeco_modern.etl.employee import import_employees_from_csv
        from zkeco_modern.etl.issuecard import import_issuecards_from_csv
        from zkeco_modern.etl.device import import_devices_from_csv
        from legacy_models.models import Employee, IssueCard, Device

        # Run ETL
        n_emp = import_employees_from_csv(emp_csv, commit=True)
        n_dev = import_devices_from_csv(dev_csv, commit=True)
        n_ic = import_issuecards_from_csv(ic_csv, commit=True)

        self.assertGreaterEqual(n_emp, 2)
        self.assertGreaterEqual(Employee.objects.count(), 2)
        self.assertGreaterEqual(n_dev, 1)
        self.assertGreaterEqual(Device.objects.count(), 1)
        self.assertGreaterEqual(n_ic, 2)
        self.assertGreaterEqual(IssueCard.objects.count(), 2)
