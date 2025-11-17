import sys
import os

print("Python executable:", sys.executable)
print("sys.path:")
for p in sys.path:
    print(" -", p)

try:
    import debug_toolbar

    print("Imported debug_toolbar from", getattr(debug_toolbar, "__file__", "unknown"))
except Exception as e:
    print("Import failed:", e)
    print("\nSearching for debug_toolbar package files on sys.path...")
    for p in sys.path:
        try:
            candidate = os.path.join(p, "debug_toolbar")
            if os.path.exists(candidate):
                print("Found folder:", candidate)
                for root, dirs, files in os.walk(candidate):
                    for f in files:
                        if f.endswith(".pyc") or f.endswith(".py"):
                            print(" -", os.path.join(root, f))
        except Exception:
            pass

# Also list django_extensions
print("\n--- django_extensions ---")
try:
    import django_extensions

    print(
        "Imported django_extensions from",
        getattr(django_extensions, "__file__", "unknown"),
    )
except Exception as e:
    print("Import failed:", e)
    for p in sys.path:
        try:
            candidate = os.path.join(p, "django_extensions")
            if os.path.exists(candidate):
                print("Found folder:", candidate)
                for root, dirs, files in os.walk(candidate):
                    for f in files:
                        if f.endswith(".pyc") or f.endswith(".py"):
                            print(" -", os.path.join(root, f))
        except Exception:
            pass
