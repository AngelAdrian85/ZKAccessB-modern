# PR: Modernize legacy Python/Django apps and improve CI/DB migration planning

## Summary

This PR continues the legacy codebase modernization effort by:

1. **Porting additional management commands** from Python 2 to Python 3/Django 4.2:
   - `zkeco/units/adms/mysite/worktable/management/commands/` (test_conn.py, instantmsg.py)
   - `zkeco/units/adms/mysite/iclock/management/commands/` (zksaas_adms.py, writedata.py, runpool.py)
   - All commands updated to: remove deprecated `option_list`, use `add_arguments()`, fix exception syntax, modernize file I/O.

2. **Added comprehensive test coverage** for ported commands:
   - `tests/test_worktable_test_conn.py` — tests DB connectivity check.
   - `tests/test_instantmsg_command.py` — tests instant messaging command.
   - `tests/test_iclock_commands.py` — tests iclock suite (zksaas_adms, writedata, runpool).
   - Tests load commands by file path to avoid package import issues in modern test environment.
   - Mocking of external dependencies (legacy models, pool servers, DB connections) ensures tests run cleanly without legacy modules.

3. **Improved CI/CD pipeline** (.github/workflows/ci.yml):
   - Added pip dependency caching (keyed on requirements files).
   - Explicit installation of dev dependencies from requirements-dev.txt.
   - Replaced shell invocations with `python -m ruff`, `python -m mypy`, `python -m pytest` for consistency.
   - Postgres service ready for integration tests.

4. **Added detailed DB migration plan** (port_plan/db_migration_plan.md):
   - Step-by-step guide for MySQL → PostgreSQL migration.
   - Comprehensive mapping notes for common type/collation incompatibilities.
   - Tools and commands for schema extraction, conversion, and data migration.
   - Rollback strategy and validation checklist.

5. **Legacy code inventory and priority list** (legacy_inventory.txt, port_plan/top_10_legacy_modules.md):
   - Scanned repo and identified 946 Python2 .pyc files and 59 .py files with legacy syntax.
   - Prioritized top-10 modules to port based on dependencies and availability of source.
   - Recommended starting with small, self-contained management commands (already started).

## Test Results

- **All tests passing**: 6 passed, 1 skipped (legacy module not importable in this environment — expected).
- **Ruff linting**: Clean on modernized code (some legacy modules in zkeco/python-support still have .pyc only, out of scope for now).
- **mypy type checking**: Passes on zkeco_modern.

## Next Steps

- Port remaining management commands and business logic from zkeco/units/adms/mysite/att and other subapps.
- Begin porting models and database layer; create Django migrations for Postgres target schema.
- Validate containerized setup with docker-compose (Postgres service ready).
- Plan data migration from legacy MySQL using pgloader or custom ETL scripts (see port_plan/db_migration_plan.md).

## Files Changed

- `.github/workflows/ci.yml` — improved CI workflow with caching and explicit pytest runner.
- `port_plan/db_migration_plan.md` — comprehensive MySQL → Postgres migration guide.
- `port_plan/top_10_legacy_modules.md` — prioritized porting roadmap.
- `legacy_inventory.txt` — legacy artifact scanner output.
- `zkeco/units/adms/mysite/worktable/management/commands/test_conn.py` — modernized.
- `zkeco/units/adms/mysite/worktable/management/commands/instantmsg.py` — modernized.
- `zkeco/units/adms/mysite/iclock/management/commands/zksaas_adms.py` — modernized.
- `zkeco/units/adms/mysite/iclock/management/commands/writedata.py` — modernized.
- `zkeco/units/adms/mysite/iclock/management/commands/runpool.py` — modernized.
- `zkeco_modern/tests/test_worktable_test_conn.py` — new test for connectivity check.
- `zkeco_modern/tests/test_instantmsg_command.py` — new test for instant messaging.
- `zkeco_modern/tests/test_iclock_commands.py` — new tests for iclock suite.

## Breaking Changes

None. Modernized commands are backward-compatible in behavior; syntax changes are internal to Django management framework.

## Related Issues

- Modernization of zkeco Django project (Python 2 → 3.11, Django 1.x → 4.2).
- Legacy infrastructure cleanup and MySQL → Postgres migration.

## Checklist

- [x] Code ported to Python 3 / Django 4.2.
- [x] Tests added and passing.
- [x] Linting (ruff) passes.
- [x] Type checking (mypy) passes.
- [x] CI workflow improved.
- [x] DB migration plan documented.
- [ ] Docker validation (pending local Docker environment).
- [ ] Data migration testing (pending staging DB setup).
