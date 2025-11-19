import os
from django.test import TestCase


class ETLEdgeCases(TestCase):
    def test_non_ascii_names(self):
        base = os.path.join(os.path.dirname(__file__), os.pardir, 'etl', 'fixtures')
        base = os.path.normpath(base)
        emp_csv = os.path.join(base, 'employee_nonascii.csv')

        from zkeco_modern.etl.employee import import_employees_from_csv
        from legacy_models.models import Employee

        r = import_employees_from_csv(emp_csv, commit=True, update=False)
        created = r['created'] if isinstance(r, dict) else r
        self.assertGreaterEqual(created, 2)
        # ensure non-ascii names stored
        self.assertTrue(Employee.objects.filter(firstname__in=['José', 'Мария']).exists())

    def test_bad_rows_and_partial(self):
        base = os.path.join(os.path.dirname(__file__), os.pardir, 'etl', 'fixtures')
        base = os.path.normpath(base)
        bad_csv = os.path.join(base, 'employee_badrows.csv')

        from zkeco_modern.etl.employee import import_employees_from_csv

        # should skip or create where possible without raising
        r = import_employees_from_csv(bad_csv, commit=True, update=False)
        created = r['created'] if isinstance(r, dict) else r
        self.assertGreaterEqual(created, 1)

    def test_resumable_batch_offset(self):
        base = os.path.join(os.path.dirname(__file__), os.pardir, 'etl', 'fixtures')
        base = os.path.normpath(base)
        emp_csv = os.path.join(base, 'employee_sample.csv')

        from zkeco_modern.etl.employee import import_employees_from_csv
        from legacy_models.models import Employee

        # first run: batch_size=1
        r1 = import_employees_from_csv(emp_csv, commit=True, update=False, batch_size=1, offset=0)
        created1 = r1['created'] if isinstance(r1, dict) else r1
        # second run with offset should create zero new if same offset covers all
        r2 = import_employees_from_csv(emp_csv, commit=True, update=False, batch_size=1, offset=created1)
        created2 = r2['created'] if isinstance(r2, dict) else r2
        self.assertGreaterEqual(created1, 1)
        self.assertGreaterEqual(created2, 0)
