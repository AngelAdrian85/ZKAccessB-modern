"""Proxy module for pytest collection.

Pytest may attempt to import `agent.test_core` depending on import resolution.
The canonical tests live in `zkeco_modern.agent.test_core`.
"""

from zkeco_modern.agent.test_core import *  # noqa: F401,F403
