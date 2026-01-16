"""Pytest bootstrap for this repo.

Why this exists:
- The real Django app package is `agent` located at `zkeco_modern/agent/`.
- When running pytest from repo root, `''` (CWD) is first on `sys.path`, which can
  cause Python/pytest to treat `zkeco_modern/` as a namespace package and import
  tests as `zkeco_modern.agent.*`. Django, however, is configured with
  `INSTALLED_APPS = ['agent', ...]`, so importing models as `zkeco_modern.agent.models`
  triggers "isn't in INSTALLED_APPS" errors.

Fix:
- Force `zkeco_modern/` to be the first import root for the test run.
- Demote/remove repo-root/CWD entries so `import agent.*` resolves consistently.
"""

import os
import sys


def _bootstrap_import_roots():
    repo_root = os.path.dirname(__file__)
    modern_root = os.path.join(repo_root, "zkeco_modern")

    # Make `zkeco_modern/` the working directory, so `''` on sys.path
    # resolves to the modern project root.
    try:
        os.chdir(modern_root)
    except Exception:
        pass

    # Ensure modern root is importable and preferred.
    try:
        while modern_root in sys.path:
            sys.path.remove(modern_root)
    except Exception:
        pass
    sys.path.insert(0, modern_root)

    # Remove repo root from sys.path so root-level shim packages (`agent/`,
    # `legacy_models/`) don't win import resolution.
    try:
        while repo_root in sys.path:
            sys.path.remove(repo_root)
    except Exception:
        pass


# Run as early as possible (module import time), before pytest-django config.
_bootstrap_import_roots()


def pytest_load_initial_conftests(*args, **kwargs):
    # Extra safety: ensure path ordering is still correct at earliest hook.
    _bootstrap_import_roots()


def pytest_configure():
    # And again at configure time, in case another plugin reordered sys.path.
    _bootstrap_import_roots()
