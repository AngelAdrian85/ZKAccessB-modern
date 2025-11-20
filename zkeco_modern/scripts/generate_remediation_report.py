#!/usr/bin/env python3
import difflib
from pathlib import Path
reports = Path(__file__).resolve().parent.parent / 'reports'
reports.mkdir(parents=True, exist_ok=True)
out = reports / 'remediation_report.txt'
root = Path(__file__).resolve().parent.parent
bak_files = list(root.rglob('*.bak'))
with out.open('w', encoding='utf-8') as f:
    f.write('Remediation report\n')
    f.write('='*60 + '\n')
    f.write(f'Found {len(bak_files)} .bak files\n\n')
    for b in bak_files:
        orig = b.with_suffix('')
        f.write(f'--- {b.relative_to(root)}\n')
        if orig.exists():
            a = orig.read_text(encoding='utf-8', errors='replace').splitlines()
            bb = b.read_text(encoding='utf-8', errors='replace').splitlines()
            diff = difflib.unified_diff(bb, a, fromfile=str(b), tofile=str(orig), lineterm='')
            f.write('\n'.join(diff))
            f.write('\n\n')
        else:
            f.write('Original file not found for this .bak: ' + str(orig) + '\n\n')
print('WROTE', out)
