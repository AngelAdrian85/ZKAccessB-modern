"""Top-level `agent` package.

This repository contains the real Django app at `zkeco_modern/agent/`.

Some tooling (pytest, scripts) runs from repo root where `''` (CWD) comes first
on `sys.path`, causing Python to import this top-level `agent/` package.

To keep imports consistent with Django `INSTALLED_APPS = ['agent', ...]`, we
extend this package's search path to include `zkeco_modern/agent/`. That makes
modules like `agent.models`, `agent.views`, `agent.middleware`, etc. load from
the real app with the correct module name (`agent.*`) instead of
`zkeco_modern.agent.*`.
"""

from pkgutil import extend_path
import os

__path__ = extend_path(__path__, __name__)  # type: ignore[name-defined]

_repo_root = os.path.dirname(os.path.dirname(__file__))
_modern_agent_dir = os.path.join(_repo_root, 'zkeco_modern', 'agent')
if os.path.isdir(_modern_agent_dir):
    # Force the modern app directory to be searched first for submodules.
    try:
        while _modern_agent_dir in __path__:
            __path__.remove(_modern_agent_dir)
    except Exception:
        pass
    __path__.insert(0, _modern_agent_dir)

    # Keep this directory (repo_root/agent) as a fallback, but lower priority.
    _this_dir = os.path.dirname(__file__)
    try:
        while _this_dir in __path__:
            __path__.remove(_this_dir)
    except Exception:
        pass
    __path__.append(_this_dir)

# Optional: expose AgentConfig for convenience (best-effort)
try:  # pragma: no cover
    from .apps import AgentConfig  # type: ignore
except Exception:  # pragma: no cover
    AgentConfig = None  # type: ignore

__all__ = ['AgentConfig']
