"""
Minimal shim package for `legacy_models` used by legacy code.

This package exists to make `import legacy_models` succeed during
`django.setup()` in validation/test environments. Keep this module
side-effect free and lightweight — it should only provide a
placeholder so imports don't raise ImportError.

If later you need to expose specific legacy modules (e.g. models,
apps), add them as submodules here or create files under
`legacy_models/` that mimic the original API.
"""
# Marker attribute for quick checks
__legacy_shim__ = True

# No heavy imports or setup here — keep it safe for django.setup().
