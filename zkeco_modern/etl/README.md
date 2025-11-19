ETL import helpers and management command

Overview
--------
This folder provides ETL importers to migrate legacy CSV exports into the `legacy_models` Django app.

Features
- idempotent update-or-create imports
- dry-run mode for safe preview
- batch-size and offset for large/resumable imports
- mapping configuration (JSON or YAML)
- management command `import_legacy` with preview and reporting

Examples (PowerShell)
----------------------
Dry-run employee import with mapping YAML preview:

```powershell
$env:DJANGO_SETTINGS_MODULE='zkeco_config.local_settings_iaccess'; $env:INCLUDE_LEGACY='1';
& 'C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB\venv311\Scripts\python.exe' manage.py import_legacy --employees zkeco_modern\etl\fixtures\employee_sample.csv --mapping zkeco_modern\etl\mapping.yaml --preview
```

Run an idempotent import (update) with batching and write a report:

```powershell
$env:DJANGO_SETTINGS_MODULE='zkeco_config.local_settings_iaccess'; $env:INCLUDE_LEGACY='1';
& 'C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB\venv311\Scripts\python.exe' manage.py import_legacy --employees zkeco_modern\etl\fixtures\employee_sample.csv --mapping zkeco_modern\etl\mapping.yaml --update --batch-size 1000 --report reports\etl_report.csv --commit
```

Best practices
- Always run with `--preview` or `--dry-run` first to validate mapping and sample rows.
- Use `--batch-size` and `--offset` for large imports and resumable runs.
- Provide a mapping YAML to avoid auto-detection mistakes; auto-detect is helpful for quick checks.
- Logs are written to `logs/etl.log` (rotating file handler).

New options and CI
------------------

- `--state-file PATH`: persist per-model offsets (JSON). When provided the importer will
	store how many rows were processed per model and will update this file after each batch.
	This enables resumable imports across interrupted runs. The stored JSON has shape:

	{
		"employee": 1234,
		"device": 456,
		"issuecard": 789
	}

- Report CSV now contains timestamp and duration columns per action: `timestamp`, `duration_s`,
	`model`, `action`, `identifier`, `pk`.

- `--preview-html PATH`: writes a richer HTML preview that includes the auto-detected mapping
	and a small table of the first N sample rows (useful during mapping validation).

CI / tests
----------

A GitHub Actions workflow is provided at `.github/workflows/ci.yml` which installs the dev
requirements and runs `pytest`. The workflow sets `DJANGO_SETTINGS_MODULE` to
`zkeco_config.local_settings_iaccess`. Adjust if you use different settings in CI.

Local test runs
---------------

When running tests locally make sure the Python path includes the `zkeco_modern` folder
so that `zkeco_config` can be imported. From PowerShell (example):

```powershell
$env:PYTHONPATH='zkeco_modern'; $env:DJANGO_SETTINGS_MODULE='zkeco_config.local_settings_iaccess'; $env:INCLUDE_LEGACY='1';
& 'C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB\venv311\Scripts\python.exe' -m pytest -q
```

If you prefer you can run pytest for a single test module (faster during development):

```powershell
$env:PYTHONPATH='zkeco_modern'; $env:DJANGO_SETTINGS_MODULE='zkeco_config.local_settings_iaccess'; $env:INCLUDE_LEGACY='1';
& 'C:\Users\AngelAdrian\Desktop\Acces\ZKAccessB\venv311\Scripts\python.exe' -m pytest zkeco_modern/tests/test_etl.py -q
```
