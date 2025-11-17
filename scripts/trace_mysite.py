import sys
import traceback
import importlib


class TraceFinder:
    def find_spec(self, fullname, path, target=None):
        if "mysite" in fullname:
            print("TRACE: import requested for", fullname)
            traceback.print_stack()
        return None


sys.meta_path.insert(0, TraceFinder())

# make sure zkeco_modern is on sys.path when running from repo root
import os  # noqa: E402

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
proj = os.path.join(root, "zkeco_modern")
if proj not in sys.path:
    sys.path.insert(0, proj)

print("sys.path[0]:", sys.path[0])

try:
    importlib.import_module("zkeco_config.settings")
    print("settings imported OK")
except Exception:
    print("Import failed:")
    traceback.print_exc()
