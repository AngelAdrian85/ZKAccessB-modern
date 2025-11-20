"""Templatetags package for legacy_models shim libraries.

This file ensures the directory is a Python package so Django can import
`zkeco_modern.legacy_models.templatetags.*` libraries when templates
use `{% load <lib> %}`. It intentionally contains no runtime side-effects.
"""

__all__ = []
