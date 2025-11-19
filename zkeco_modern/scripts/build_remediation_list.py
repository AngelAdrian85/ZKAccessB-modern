import json
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(__file__)
REPORT = os.path.join(ROOT, 'sanitize_report.json')
APPLY_LOG = os.path.join(ROOT, 'apply_sanitized_log.json')
OUT = os.path.join(ROOT, 'remediation_list.json')

if not os.path.exists(REPORT):
    print('no report')
    raise SystemExit(1)

with open(REPORT, 'r', encoding='utf-8') as fh:
    report = json.load(fh)

errors = [f.get('error') for f in report.get('failed', [])]
errcount = Counter(errors)

by_error = defaultdict(list)
for f in report.get('failed', []):
    by_error[f.get('error')].append(f.get('file'))

summary = {
    'total_processed': len(report.get('processed', [])),
    'total_failed': len(report.get('failed', [])),
    'error_counts': errcount.most_common(),
    'top_files_per_error': {k: v[:20] for k, v in by_error.items()}
}

with open(OUT, 'w', encoding='utf-8') as fh:
    json.dump(summary, fh, ensure_ascii=False, indent=2)

print('remediation list written to', OUT)
