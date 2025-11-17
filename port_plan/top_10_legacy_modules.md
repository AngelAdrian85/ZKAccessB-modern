# Top-10 legacy modules to port (prioritized)

This list was created from the legacy scanner snapshot (`legacy_inventory.txt`). It prioritizes modules that:
- are likely required by many parts of the system (high dependency),
- have source `.py` files present (so porting is feasible), and
- are relatively self-contained so we can port incrementally and test.

1. `zkeco/units/adms/mysite/att` (management commands and small app files)
   - Why: contains `.py` sources. Small, self-contained pieces (e.g. `autocalculate.py`) that are good first ports.
2. `zkeco/units/adms/mysite/worktable` (management commands)
   - Why: contains helper commands used by adms workflows. Low-risk to port and add tests.
3. `zkeco/units/adms/mysite/iclock` (management commands / device comms)
   - Why: contains device communication scripts; important but keep tests small.
4. `zkeco/python-support/base` (models, modeladmin, cached_model)
   - Why: high-impact (models/shared logic) but many files are only present as `.pyc` in the repo — may require recovering source from other copy or decompilation.
5. `zkeco/python-support/wsgiserver` / `svr8000` / `report.py`
   - Why: low-level servers and utilities. Port if needed for runtime.
6. `zkeco/python-support/piston` (API helpers)
   - Why: legacy API library; replace with Django REST Framework where applicable.
7. `zkeco/python-support/pyDes` and `pyExcelerator` helpers
   - Why: third-party helpers, consider replacing with maintained libraries (pycryptodome, openpyxl).
8. `zkeco/python-support/debug_toolbar` / `django_extensions` pieces
   - Why: developer tooling; port or replace with modern equivalents.
9. `zkeco/units/*` additional small apps (pick per-dependency)
   - Why: contains domain logic split into units; port incrementally per unit.
10. `zkeco/python-support/redis` / `johnny` wrappers
   - Why: caching/backends — port carefully, verify compatibility.

Recommended first target: `zkeco/units/adms/mysite/att/autocalculate.py` — it's small, has clear behavior, and can be ported and tested independently.

Next actions (automated if you say go):
- create branch `port/python3/att-autocalculate` and commit a Python3/Django4-compatible version of `autocalculate.py`.
- run ruff/mypy/pytest to confirm no regressions.
