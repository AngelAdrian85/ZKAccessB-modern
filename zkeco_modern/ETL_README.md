ETL: state-file and flush interval

New CLI options in `import_legacy`:

- `--state-file PATH` : path to JSON file used to persist per-model offsets so imports can resume.
- `--state-flush-interval N` : write the state file only when processed rows reach multiples of N. Default is `1` (write every row).
- `--state-dry-run` : allow state-file updates while running with `--dry-run` (opt-in).

Settings:

- `IACCESS_STATE_FLUSH_INTERVAL` : optional Django setting. If present, it overrides the default flush-interval (only when the CLI value is left as default).
- `IACCESS_LOG_CSV_ALLOWED_GROUPS` : list of group names allowed to export CSV logs (in addition to `is_staff`).
- `IACCESS_LOG_CSV_REQUIRE_STAFF` : default `True`. If set to `False`, the logs export does not require staff membership.

Examples

Write state every 10 rows:

```powershell
set PYTHONPATH=zkeco_modern ; set DJANGO_SETTINGS_MODULE=zkeco_config.local_settings_iaccess ; \
.\venv311\Scripts\python.exe manage.py import_legacy --employees employees.csv --state-file state.json --state-flush-interval 10 --commit --report report.csv
```

Allow dry-run to update state (simulate progress):

```powershell
set PYTHONPATH=zkeco_modern ; set DJANGO_SETTINGS_MODULE=zkeco_config.local_settings_iaccess ; \
.\venv311\Scripts\python.exe manage.py import_legacy --employees employees.csv --state-file state.json --state-dry-run --dry-run
```

Notes

- The command persists the final state after each model import completes (unless `--dry-run` without `--state-dry-run`).
- For very large imports you can increase `--state-flush-interval` to reduce I/O; smaller intervals improve resume granularity.
