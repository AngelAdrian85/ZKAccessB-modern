#!/usr/bin/env python3
"""Apply validated template patches safely.

Reads `validation_report.json` and for each `validated` entry:
- creates a `.bak` of the original template (if exists and not already backed up)
- copies the patch content into the original template path
- records actions in `scripts/applied_patches.json`.

This is non-reversible except for the .bak files; review before committing.
"""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'zkeco_modern' / 'scripts'
REPORT = SCRIPTS / 'validation_report.json'
APPLIED = SCRIPTS / 'applied_patches.json'

def main():
    if not REPORT.exists():
        print('Missing validation report:', REPORT)
        return 2
    data = json.loads(REPORT.read_text(encoding='utf-8'))
    validated = data.get('validated', [])
    applied = []

    for ent in validated:
        orig = Path(ent['file'])
        patch = Path(ent['patch'])
        if not patch.exists():
            applied.append({'file': str(orig), 'status': 'patch_missing'})
            continue
        # create backup if original exists
        if orig.exists():
            bak = orig.with_suffix(orig.suffix + '.bak')
            if not bak.exists():
                bak.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(orig, bak)
        else:
            # ensure directory exists for new file
            orig.parent.mkdir(parents=True, exist_ok=True)

        # copy patch into place
        shutil.copy2(patch, orig)
        applied.append({'file': str(orig), 'patch': str(patch), 'status': 'applied'})

    APPLIED.write_text(json.dumps({'applied': applied}, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Applied', len(applied), 'patches; log at', APPLIED)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
