"""
Top-level shim package for `iaccess_port` that forwards to
the `zkeco_modern.iaccess_port` package so imports like
`import iaccess_port` succeed during tests and Django setup.

This keeps the project layout intact while allowing tests
that expect `iaccess_port` at top-level to work.
"""
from importlib import import_module
import sys

# Import the real module from the `zkeco_modern` package and insert it
# into sys.modules under the top-level name so other imports succeed.
_real_name = "zkeco_modern.iaccess_port"
try:
    _mod = import_module(_real_name)
    sys.modules[__name__] = _mod
except Exception:
    # If the real package isn't available yet, keep this module minimal.
    pass
