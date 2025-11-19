import json
import tempfile
from pathlib import Path
from django.core.management import call_command
from legacy_models.models import Employee
import pytest


def _write_row(path, userid, badgenumber, firstname='Fn', lastname='Ln'):
    line = f"{userid},{badgenumber},{firstname},{lastname},000{userid},001,{firstname}.{lastname}@example.local,ID{userid},2020-01-01,2025-01-01,Sales\n"
    with open(path, 'a', encoding='utf-8', newline='') as fh:
        fh.write(line)


@pytest.mark.django_db
def test_state_flush_interval_behaviour(tmp_path):
    # create temp CSV with one row, flush interval 2 => state should NOT be persisted after first run
    csv_path = tmp_path / 'employees.csv'
    state_file = tmp_path / 'state' / 'etl_state.json'
    report_file = tmp_path / 'report.csv'

    # write first row only
    csv_path.write_text('userid,badgenumber,firstname,lastname,card_number,site_code,email,identitycard,acc_startdate,acc_enddate,deptname\n', encoding='utf-8')
    _write_row(csv_path, 4001, 4001, 'Alpha', 'One')

    # run with flush interval 2 (so state should not be written after 1 row)
    call_command('import_legacy', employees=str(csv_path), commit=True, state_file=str(state_file), report=str(report_file), state_flush_interval='2')

    if state_file.exists():
        s = json.loads(state_file.read_text(encoding='utf-8'))
        assert int(s.get('employee', 0)) == 0

    # append second row and rerun; now total 2 rows -> flush interval reached -> state should be 2
    _write_row(csv_path, 4002, 4002, 'Beta', 'Two')
    call_command('import_legacy', employees=str(csv_path), commit=True, state_file=str(state_file), report=str(report_file), state_flush_interval='2')

    assert state_file.exists()
    s = json.loads(state_file.read_text(encoding='utf-8'))
    assert int(s.get('employee', 0)) == 2

    # DB should have two employee records
    assert Employee.objects.filter(userid__in=[4001, 4002]).count() == 2
