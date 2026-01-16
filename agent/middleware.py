"""Proxy module for backward-compatible imports.

Some tooling (pytest, scripts) may import `agent.middleware` while running from repo root,
which would otherwise resolve to this top-level `agent/` package.

The real implementation lives in `zkeco_modern.agent.middleware`.
"""

from zkeco_modern.agent.middleware import *  # noqa: F401,F403
