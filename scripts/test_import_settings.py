import importlib
import traceback

try:
    importlib.import_module("zkeco_config.settings")
    print("Imported settings OK")
except Exception:
    print("Import failed:")
    traceback.print_exc()
