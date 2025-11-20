# shim package so imports like `import zkeco_config` work during tests
from importlib import import_module
_real = import_module('zkeco_modern.zkeco_config')
# re-export attributes to emulate the original package
for _name in dir(_real):
    if not _name.startswith('_'):
        globals()[_name] = getattr(_real, _name)
