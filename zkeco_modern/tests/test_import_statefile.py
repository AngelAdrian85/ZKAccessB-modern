import json
import tempfile
from pathlib import Path
from django.test import TestCase
from django.core.management import call_command
from legacy_models.models import Employee

class ImportStateFileTests(TestCase):
    def test_import_resume_statefile(self):
        # We'll create a small CSV and simulate an interrupted import by
        # writing one row first, running import_legacy, then appending rows
        # and running again to validate the state-file resume behavior.
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / 'employees.csv'
            state_file = Path(td) / 'state' / 'etl_state.json'
            report_file = Path(td) / 'report.csv'

            # write first row only
            csv_path.write_text('userid,badgenumber,firstname,lastname,card_number,site_code,email,identitycard,acc_startdate,acc_enddate,deptname\n3001,3001,Alpha,One,0003001,003,alpha.one@example.local,ID3001,2020-01-01,2025-01-01,Sales\n', encoding='utf-8')

            # First run: process the single-row CSV
            call_command('import_legacy', employees=str(csv_path), commit=True, state_file=str(state_file), report=str(report_file))

            # State file should exist and show progress of 1
            assert state_file.exists()
            s = json.loads(state_file.read_text(encoding='utf-8'))
            self.assertIn('employee', s)
            self.assertEqual(int(s.get('employee', 0)), 1)

            # Append a second row to the CSV to simulate new data after interruption
            with open(csv_path, 'a', encoding='utf-8', newline='') as fh:
                fh.write('3002,3002,Beta,Two,0003002,003,beta.two@example.local,ID3002,2021-02-02,2026-02-02,Engineering\n')

            # Second run: resume using same state file
            call_command('import_legacy', employees=str(csv_path), commit=True, state_file=str(state_file), report=str(report_file))

            # Now state should reflect both rows processed (2)
            s2 = json.loads(state_file.read_text(encoding='utf-8'))
            self.assertEqual(int(s2.get('employee', 0)), 2)

            # Database should have two Employee rows
            self.assertEqual(Employee.objects.count(), 2)
