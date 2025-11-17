import re
from pathlib import Path

ROOT = Path('.').resolve()
EXCLUDE_DIRS = {'venv311', 'venv', 'env', 'venv3', '.venv', '.git', 'node_modules'}

py_files = [p for p in ROOT.rglob('*.py') if not any(part in EXCLUDE_DIRS for part in p.parts)]

# Patterns
re_eq_none = re.compile(r'(?<![=!<>])==\s*None')
re_neq_none = re.compile(r'!=\s*None')
re_single_if_return = re.compile(r'^(?P<indent>\s*)if\s+(?P<cond>[^:]+):\s*return\s+(?P<expr>.+)$', re.MULTILINE)
re_lambda_assign = re.compile(r'^(?P<indent>\s*)(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*lambda\s*(?P<args>[^:]*?):\s*(?P<body>.+)$', re.MULTILINE)

changed_files = []
for p in py_files:
    try:
        src = p.read_text(encoding='utf-8')
    except Exception:
        continue
    original = src
    # Replace comparisons to None
    src = re_neq_none.sub(' is not None', src)
    src = re_eq_none.sub(' is None', src)

    # Replace single-line if-return with multi-line
    def _ifret(m):
        indent = m.group('indent')
        cond = m.group('cond').strip()
        expr = m.group('expr').strip()
        return f"{indent}if {cond}:\n{indent}    return {expr}"
    src = re_single_if_return.sub(_ifret, src)

    # Replace simple lambda assignments with defs (very conservative)
    def _lambda_to_def(m):
        indent = m.group('indent')
        name = m.group('name')
        args = m.group('args').strip()
        body = m.group('body').strip()
        # refuse if body contains ':' or 'lambda' or 'def' to avoid complex cases
        if ':' in body or 'lambda' in body or ' def ' in body:
            return m.group(0)
        # ensure args parentheses
        args = args.strip()
        # build def
        return f"{indent}def {name}({args}):\n{indent}    return {body}"
    src = re_lambda_assign.sub(_lambda_to_def, src)

    if src != original:
        p.write_text(src, encoding='utf-8')
        changed_files.append(str(p))

print('Files changed:', len(changed_files))
for f in changed_files:
    print(' -', f)

if not changed_files:
    print('No changes applied.')
