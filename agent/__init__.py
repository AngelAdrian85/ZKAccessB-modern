# Root-level agent proxy to expose older import style.
from importlib import import_module as _im
_pkg = _im('zkeco_modern.agent')
# Expose app config & key modules; avoid pulling everything to reduce noise.
try:
    apps = _im('zkeco_modern.agent.apps')
    AgentConfig = getattr(apps, 'AgentConfig')
except Exception:
    pass
try:
    views = _im('zkeco_modern.agent.views')
except Exception:
    views = None
__all__ = ['AgentConfig','views']
