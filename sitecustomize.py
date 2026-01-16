# sitecustomize.py — executed at Python startup (if CWD is on sys.path)
# Purpose: remove known legacy vendor/installer paths that contain Python2 .pyc files
# so they don't interfere with running the modern code in this repository.
import sys
import os

_bad_markers = ("ZKTeco", "python-support", "Python26", os.path.join("zkeco", "units"))


def _ensure_modern_on_path():
    """Ensure the modern Django project root (`zkeco_modern/`) is importable.

    Pytest imports tests as `agent.*` (module inside `zkeco_modern/agent`).
    When running from repo root, adding `zkeco_modern` to sys.path makes that work.
    """
    try:
        repo_root = os.path.dirname(__file__)
        modern_dir = os.path.join(repo_root, 'zkeco_modern')
        if not os.path.isdir(modern_dir):
            return

        # Remove existing occurrences
        sys.path[:] = [p for p in sys.path if p not in (modern_dir,)]

        # Force modern_dir to the very front.
        sys.path.insert(0, modern_dir)

        # Move CWD entry (""), and repo_root after modern_dir so `import agent`
        # resolves to `zkeco_modern/agent` (the installed Django app), not the
        # root-level proxy package and not the `zkeco_modern.*` namespace package.
        for special in ('', repo_root):
            try:
                while special in sys.path[0:2]:
                    sys.path.remove(special)
            except Exception:
                pass
        # Re-add repo_root and CWD entry after modern_dir (keep behavior but lower priority)
        if repo_root not in sys.path:
            sys.path.insert(1, repo_root)
        if '' not in sys.path:
            sys.path.insert(2, '')
    except Exception:
        return


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
_ensure_modern_on_path()
_filter_sys_path()
