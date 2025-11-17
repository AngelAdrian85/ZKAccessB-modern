# PR: CI + tests + smoke checks

Summary
-------
This changeset adds CI and repository hygiene improvements and a small, fast end-to-end test plus a smoke-check script used during development.

What I changed
- Added a GitHub Actions CI workflow (matrix for Python and DB backends).
- Added `.pre-commit-config.yaml` with ruff and basic hooks.
- Added `scripts/create_ci_admin.py` and `scripts/smoke_check.py` for local/dev runs.
- Added a small pytest-django e2e test: `zkeco_modern/tests/test_e2e_login_create_user.py` that creates a test superuser and verifies admin access.

Why
---
These changes make it easier to run deterministic linting and tests locally and in CI, and provide a minimal smoke/e2e test to catch obvious regressions.

Files to review
- .github/workflows/ci.yml
- .pre-commit-config.yaml
- scripts/create_ci_admin.py
- scripts/smoke_check.py
- zkeco_modern/tests/test_e2e_login_create_user.py

Notes
-----
- The dev server is NOT production ready and should not be exposed publicly.
- I could not create a remote PR from the agent because the environment lacked git access; please run the recommended git commands locally and open the PR.
