# sitecustomize.py — executed at Python startup (if CWD is on sys.path)
# Purpose: remove known legacy vendor/installer paths that contain Python2 .pyc files
# so they don't interfere with running the modern code in this repository.
import sys
import os

_bad_markers = ("ZKTeco", "python-support", "Python26", os.path.join("zkeco", "units"))


def _filter_sys_path():
    removed = []
    new = []
    for p in sys.path:
        if not p:
            new.append(p)
            continue
        try:
            if any(marker in p for marker in _bad_markers):
                removed.append(p)
            else:
                new.append(p)
        except Exception:
            new.append(p)
    if removed:
        # update sys.path in-place
        sys.path[:] = new
        # best-effort log to stderr — avoid failing startup
        try:
            sys.stderr.write("[sitecustomize] removed legacy paths:\n")
            for r in removed:
                sys.stderr.write("  " + r + "\n")
        except Exception:
            pass


# Run the filter as early as possible
_filter_sys_path()
