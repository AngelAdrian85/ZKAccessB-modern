# DB migration runbook — draft

This document is a first-draft runbook to migrate legacy data into the reconstructed Django models in `zkeco_modern/legacy_models`.

Scope
- Local-first, non-destructive steps to export data from an existing legacy DB and import into the new Django models (for testing). Production migration will need additional verification and mapping.

High-level steps
1. Backup the existing production database (FULL BACKUP). Keep copies offsite.
2. Snapshot the application files and configuration (copy `zkeco/units/adms/mysite` and `python-support`).
3. Create a local migration environment (this repository) and ensure the local settings override `zkeco_modern/zkeco_config/local_settings_iaccess.py` is used when running commands below.

Local dev commands (examples)
```powershell
& .\venv311\Scripts\python.exe -m django makemigrations legacy_models --settings=zkeco_config.local_settings_iaccess
& .\venv311\Scripts\python.exe -m django migrate --settings=zkeco_config.local_settings_iaccess
& .\venv311\Scripts\python.exe -m django loaddata zkeco_modern/legacy_models/fixtures/initial_data.json --settings=zkeco_config.local_settings_iaccess
```

Mapping notes (examples inferred from templates)
- Legacy table `userinfo` → `legacy_models.Employee`
  - `userid` → `userid` (Integer)
  - `badgenumber` → `badgenumber`
  - `name` → `firstname` / `lastname` (split as needed)
  - `card_number` / `card_no` → `card_number`
  - `site_code` → `site_code`
  - `email` → `email`
  - `identitycard` → `identitycard`
  - `acc_startdate`/`acc_enddate` → `acc_startdate` / `acc_enddate`

- Legacy table `personnel_issuecard` → `legacy_models.IssueCard`
  - `cardno` → `cardno`
  - `cardstatus` → `cardstatus`
  - `userid_id` → `userid` (FK to Employee)

- Legacy table `iclock.Device` → `legacy_models.Device`
  - `sn` → `sn`
  - `device_name` → `device_name`
  - `area` → `area` (map to `legacy_models.Area`)

Recommended data-migration approach
1. Export legacy tables to CSV (or SQL dumps) for the tables listed above.
2. Create mapping/ETL scripts (Python) that read exported CSVs and transform them to the Django model field names and formats. For example:
   - Parse `name` columns into `firstname`/`lastname` if needed.
   - Convert date formats to ISO (YYYY-MM-DD).
   - Normalize card numbers (strip leading zeros if needed).
3. Run the mapping script locally against the Django ORM using `manage.py shell` and `bulk_create` inside a transaction. Example:
```python
from legacy_models.models import Employee
from django.db import transaction

with transaction.atomic():
    objs = [Employee(userid=..., firstname=..., ...), ...]
    Employee.objects.bulk_create(objs)
```
4. Verify counts and sample records. Compare a few sample rows with the legacy DB.

Rollback
- Keep the original exported CSVs/SQL dumps. If import is wrong, drop the imported rows and re-run the ETL with fixes.

Next steps
- Expand this runbook with exact SQL/CSV export commands for your production DB (MySQL/SQL Server/Oracle). Add sample ETL scripts and verification queries.
- Add integration tests that validate the imported data against known legacy outputs.

Database export examples

MySQL (example using mysqldump to export a single table to CSV via SELECT INTO OUTFILE):

```sql
-- from mysql client
SELECT userid,badgenumber,firstname,lastname,card_number,site_code,email,identitycard,acc_startdate,acc_enddate,DeptName
INTO OUTFILE '/tmp/userinfo.csv'
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
FROM userinfo;
```

Or use `mysqldump` and convert SQL to CSV with `csvkit` or a small parser.

SQL Server (bcp utility example):

```powershell
bcp "SELECT userid,badgenumber,firstname,lastname,card_number,site_code,email,identitycard,acc_startdate,acc_enddate,DeptName FROM mydb.dbo.userinfo" queryout C:\temp\userinfo.csv -c -t, -S myserver -U myuser -P mypassword
```

Oracle (SQL*Plus/SQLcl example to spool CSV):

```sql
SET COLSEP ','
SET PAGESIZE 0
SET TRIMSPOOL ON
SPOOL /tmp/userinfo.csv
SELECT userid||','||badgenumber||','||firstname||','||lastname||','||card_number||','||site_code||','||email||','||identitycard||','||TO_CHAR(acc_startdate,'"YYYY-MM-DD"') FROM userinfo;
SPOOL OFF
```

Notes:
- Replace table and column names with the real legacy DB names. The commands above are examples — test them in a non-production environment first.
- If the DB user cannot write files on the DB host, export via client tools (`mysqldump`, `bcp`, `sqlcmd`, `SQLcl`) from a machine that can reach the DB and save CSV locally.

