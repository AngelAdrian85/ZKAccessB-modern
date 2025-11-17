"""Scan the workspace for likely Python2-era artifacts.

Checks performed:
- .pyc files with Python 2 magic header
- .py files containing "print " statements without parentheses (heuristic)
- files under known legacy folders (zkeco/python-support, Python26)

Run from repo root: python scripts/find_legacy_py2_files.py
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Python 2 .pyc magic header sequence (may vary by minor versions), common marker discovered earlier
PY2_MAGIC = b"\xd1\xf2\r\n"

def scan_pyc(path: Path):
    found = []
    for p in path.rglob('*.pyc'):
        try:
            with p.open('rb') as fh:
                header = fh.read(4)
            if header == PY2_MAGIC:
                found.append(p)
        except Exception:
            continue
    return found

def scan_print_statements(path: Path):
    found = []
    for p in path.rglob('*.py'):
        try:
            text = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        # crude heuristic: lines starting with print followed by space (not function)
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith('print ') and not stripped.startswith('print('):
                found.append((p, i, line.strip()))
                break
    return found

def scan_legacy_dirs(path: Path):
    markers = ['ZKTeco', 'python-support', 'Python26', 'zkeco\\units']
    found = []
    for p in path.rglob('*'):
        if any(m in str(p) for m in markers):
            found.append(p)
    return found

def main():
    print(f"Scanning repository: {REPO_ROOT}")

    pyc_legacy = scan_pyc(REPO_ROOT)
    print(f"Found {len(pyc_legacy)} .pyc files with Python2 magic (showing up to 20):")
    for p in pyc_legacy[:20]:
        print('  ', p)

    print('\nScanning for legacy print statements in .py files...')
    prints = scan_print_statements(REPO_ROOT)
    print(f"Found {len(prints)} .py files with legacy print statements (showing up to 20):")
    for p, ln, txt in prints[:20]:
        print(f'  {p}:{ln}: {txt}')

    print('\nScanning for files in known legacy directories...')
    legacy = scan_legacy_dirs(REPO_ROOT)
    print(f"Found {len(legacy)} items matching legacy markers (showing up to 20):")
    for p in legacy[:20]:
        print('  ', p)

    print('\nDone. Use these results to pick modules to port.')

if __name__ == '__main__':
    main()
